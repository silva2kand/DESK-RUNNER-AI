"""Speech recognition and synthesis handler with Tamil/English support."""

import asyncio
import logging
import threading
from typing import Optional, Callable, Dict, Any
from queue import Queue, Empty

try:
    import speech_recognition as sr
    import pyttsx3
    from langdetect import detect
    from googletrans import Translator
except ImportError as e:
    logging.warning(f"Speech dependencies not available: {e}")
    sr = None
    pyttsx3 = None

from .config import SpeechConfig


class SpeechHandler:
    """Handles speech recognition and text-to-speech with multilingual support."""
    
    def __init__(self, config: SpeechConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.recognizer = None
        self.microphone = None
        self.tts_engine = None
        self.translator = None
        
        # State management
        self.is_listening = False
        self.current_language = config.default_language
        self.speech_queue = Queue()
        
        # Callbacks
        self.on_speech_recognized: Optional[Callable[[str, str], None]] = None
        self.on_speech_error: Optional[Callable[[str], None]] = None
        
        # Initialize if dependencies are available
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize speech recognition and synthesis components."""
        try:
            if sr is None:
                self.logger.warning("Speech recognition not available")
                return
                
            # Initialize speech recognition
            self.recognizer = sr.Recognizer()
            self.microphone = sr.Microphone()
            
            # Adjust for ambient noise
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source)
            
            # Initialize text-to-speech
            if pyttsx3:
                self.tts_engine = pyttsx3.init()
                self._configure_tts()
            
            # Initialize translator for Tamil support
            self.translator = Translator()
            
            self.logger.info("Speech components initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize speech components: {e}")
    
    def _configure_tts(self):
        """Configure text-to-speech engine."""
        if not self.tts_engine:
            return
            
        try:
            # Set speech rate
            self.tts_engine.setProperty('rate', self.config.speech_rate)
            
            # Set volume
            self.tts_engine.setProperty('volume', self.config.speech_volume)
            
            # Try to set language-appropriate voice
            voices = self.tts_engine.getProperty('voices')
            if voices:
                # Look for Tamil or English voices
                for voice in voices:
                    if 'tamil' in voice.name.lower() or 'ta' in voice.id.lower():
                        if self.current_language.startswith('ta'):
                            self.tts_engine.setProperty('voice', voice.id)
                            break
                    elif 'english' in voice.name.lower() or 'en' in voice.id.lower():
                        if self.current_language.startswith('en'):
                            self.tts_engine.setProperty('voice', voice.id)
                            break
                            
        except Exception as e:
            self.logger.warning(f"TTS configuration warning: {e}")
    
    def start_listening(self) -> bool:
        """Start continuous speech recognition."""
        if not self.recognizer or not self.microphone:
            self.logger.error("Speech recognition not available")
            return False
            
        if self.is_listening:
            self.logger.warning("Already listening")
            return True
            
        try:
            self.is_listening = True
            
            # Start listening in background thread
            self.recognizer.listen_in_background(
                self.microphone,
                self._on_audio_received,
                phrase_time_limit=self.config.phrase_timeout
            )
            
            self.logger.info("Started speech recognition")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start listening: {e}")
            self.is_listening = False
            return False
    
    def stop_listening(self):
        """Stop speech recognition."""
        self.is_listening = False
        self.logger.info("Stopped speech recognition")
    
    def _on_audio_received(self, recognizer, audio):
        """Handle received audio data."""
        if not self.is_listening:
            return
            
        try:
            # Try to recognize speech
            text = self._recognize_speech(audio)
            if text:
                # Detect language
                detected_lang = self._detect_language(text)
                self.logger.debug(f"Recognized speech: '{text}' (language: {detected_lang})")
                
                # Call callback if set
                if self.on_speech_recognized:
                    self.on_speech_recognized(text, detected_lang)
                    
        except Exception as e:
            self.logger.error(f"Speech recognition error: {e}")
            if self.on_speech_error:
                self.on_speech_error(str(e))
    
    def _recognize_speech(self, audio) -> Optional[str]:
        """Recognize speech from audio data."""
        try:
            # Try Google Speech Recognition first
            if self.config.recognition_engine == "google":
                # Try current language first
                try:
                    text = self.recognizer.recognize_google(
                        audio, 
                        language=self.current_language,
                        timeout=self.config.recognition_timeout
                    )
                    return text
                except sr.UnknownValueError:
                    # Try other supported languages
                    for lang in self.config.languages:
                        if lang != self.current_language:
                            try:
                                text = self.recognizer.recognize_google(
                                    audio, 
                                    language=lang,
                                    timeout=self.config.recognition_timeout
                                )
                                return text
                            except sr.UnknownValueError:
                                continue
            
            # Fallback to Sphinx if available
            try:
                return self.recognizer.recognize_sphinx(audio)
            except sr.UnknownValueError:
                pass
                
        except sr.RequestError as e:
            self.logger.error(f"Speech recognition service error: {e}")
        except Exception as e:
            self.logger.error(f"Speech recognition error: {e}")
            
        return None
    
    def _detect_language(self, text: str) -> str:
        """Detect language of recognized text."""
        try:
            detected = detect(text)
            
            # Map detected language to our supported languages
            if detected == 'ta':
                return 'ta-IN'
            elif detected == 'en':
                return 'en-US'
            else:
                return self.current_language
                
        except Exception as e:
            self.logger.warning(f"Language detection failed: {e}")
            return self.current_language
    
    def speak(self, text: str, language: Optional[str] = None) -> bool:
        """Convert text to speech."""
        if not self.tts_engine:
            self.logger.warning("TTS engine not available")
            return False
            
        try:
            # Use specified language or current language
            target_lang = language or self.current_language
            
            # Translate if needed
            if target_lang.startswith('ta') and self._is_english_text(text):
                text = self._translate_text(text, 'ta')
            elif target_lang.startswith('en') and self._is_tamil_text(text):
                text = self._translate_text(text, 'en')
            
            # Update TTS configuration for language
            if target_lang != self.current_language:
                self.current_language = target_lang
                self._configure_tts()
            
            # Speak the text
            self.tts_engine.say(text)
            self.tts_engine.runAndWait()
            
            return True
            
        except Exception as e:
            self.logger.error(f"TTS error: {e}")
            return False
    
    def _is_english_text(self, text: str) -> bool:
        """Check if text is primarily English."""
        try:
            detected = detect(text)
            return detected == 'en'
        except:
            # Fallback: check for ASCII characters
            return all(ord(char) < 128 for char in text if char.isalpha())
    
    def _is_tamil_text(self, text: str) -> bool:
        """Check if text contains Tamil characters."""
        try:
            detected = detect(text)
            return detected == 'ta'
        except:
            # Fallback: check for Tamil Unicode range
            return any(0x0B80 <= ord(char) <= 0x0BFF for char in text)
    
    def _translate_text(self, text: str, target_lang: str) -> str:
        """Translate text to target language."""
        if not self.translator:
            return text
            
        try:
            result = self.translator.translate(text, dest=target_lang)
            return result.text
        except Exception as e:
            self.logger.warning(f"Translation failed: {e}")
            return text
    
    def set_language(self, language: str):
        """Set the current language for recognition and synthesis."""
        if language in self.config.languages:
            self.current_language = language
            self._configure_tts()
            self.logger.info(f"Language set to: {language}")
        else:
            self.logger.warning(f"Unsupported language: {language}")
    
    def get_available_languages(self) -> list:
        """Get list of available languages."""
        return self.config.languages.copy()
    
    async def listen_once(self, timeout: float = 5.0) -> Optional[str]:
        """Listen for a single phrase and return recognized text."""
        if not self.recognizer or not self.microphone:
            return None
            
        try:
            # Listen for audio
            with self.microphone as source:
                self.logger.debug("Listening for speech...")
                audio = self.recognizer.listen(source, timeout=timeout)
            
            # Recognize speech
            text = self._recognize_speech(audio)
            return text
            
        except sr.WaitTimeoutError:
            self.logger.debug("Listen timeout")
            return None
        except Exception as e:
            self.logger.error(f"Listen error: {e}")
            return None