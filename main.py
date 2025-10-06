#!/usr/bin/env python3
"""
DESK-RUNNER-AI - Desktop Listen and Runner AI
Main entry point for the desktop AI application
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import queue
import speech_recognition as sr
import pyttsx3
import logging
import time
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DeskRunnerAI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("DESK-RUNNER-AI - Desktop Listen and Runner AI")
        self.root.geometry("800x600")
        
        # Initialize components
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.tts_engine = pyttsx3.init()
        
        # Threading and communication
        self.command_queue = queue.Queue()
        self.response_queue = queue.Queue()
        self.is_listening = False
        self.listen_thread = None
        
        # Setup GUI
        self.setup_gui()
        
        # Setup speech recognition
        self.setup_speech_recognition()
        
        logger.info("DESK-RUNNER-AI initialized successfully")
    
    def setup_gui(self):
        """Setup the main GUI interface"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="DESK-RUNNER-AI", font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 10))
        
        # Status frame
        status_frame = ttk.Frame(main_frame)
        status_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        status_frame.columnconfigure(1, weight=1)
        
        ttk.Label(status_frame, text="Status:").grid(row=0, column=0, padx=(0, 10))
        self.status_var = tk.StringVar(value="Ready")
        self.status_label = ttk.Label(status_frame, textvariable=self.status_var, foreground="green")
        self.status_label.grid(row=0, column=1, sticky=tk.W)
        
        # Control buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=1, column=2, padx=(10, 0))
        
        self.listen_button = ttk.Button(button_frame, text="Start Listening", command=self.toggle_listening)
        self.listen_button.grid(row=0, column=0, padx=(0, 5))
        
        self.clear_button = ttk.Button(button_frame, text="Clear Log", command=self.clear_log)
        self.clear_button.grid(row=0, column=1)
        
        # Log area
        log_frame = ttk.LabelFrame(main_frame, text="Activity Log", padding="5")
        log_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=20, width=80)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Command input area
        input_frame = ttk.LabelFrame(main_frame, text="Manual Command Input", padding="5")
        input_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
        input_frame.columnconfigure(0, weight=1)
        
        self.command_entry = ttk.Entry(input_frame, font=("Arial", 10))
        self.command_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 10))
        self.command_entry.bind('<Return>', self.process_manual_command)
        
        self.send_button = ttk.Button(input_frame, text="Send", command=self.process_manual_command)
        self.send_button.grid(row=0, column=1)
        
        # Initialize log with welcome message
        self.log_message("DESK-RUNNER-AI started successfully")
        self.log_message("Click 'Start Listening' to begin voice recognition")
        self.log_message("Or type commands manually in the input field below")
    
    def setup_speech_recognition(self):
        """Setup speech recognition with microphone calibration"""
        try:
            with self.microphone as source:
                self.log_message("Calibrating microphone for ambient noise...")
                self.recognizer.adjust_for_ambient_noise(source)
            self.log_message("Microphone calibration complete")
        except Exception as e:
            self.log_message(f"Error setting up microphone: {str(e)}")
            logger.error(f"Microphone setup error: {e}")
    
    def log_message(self, message):
        """Add message to the log with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}\n"
        
        self.log_text.insert(tk.END, formatted_message)
        self.log_text.see(tk.END)
        self.root.update_idletasks()
        
        logger.info(message)
    
    def clear_log(self):
        """Clear the activity log"""
        self.log_text.delete(1.0, tk.END)
        self.log_message("Log cleared")
    
    def toggle_listening(self):
        """Toggle voice listening on/off"""
        if not self.is_listening:
            self.start_listening()
        else:
            self.stop_listening()
    
    def start_listening(self):
        """Start voice listening in a separate thread"""
        self.is_listening = True
        self.listen_button.config(text="Stop Listening")
        self.status_var.set("Listening...")
        self.status_label.config(foreground="red")
        
        self.listen_thread = threading.Thread(target=self.listen_for_commands, daemon=True)
        self.listen_thread.start()
        
        self.log_message("Voice listening started - speak your commands")
    
    def stop_listening(self):
        """Stop voice listening"""
        self.is_listening = False
        self.listen_button.config(text="Start Listening")
        self.status_var.set("Ready")
        self.status_label.config(foreground="green")
        
        self.log_message("Voice listening stopped")
    
    def listen_for_commands(self):
        """Listen for voice commands in a loop"""
        while self.is_listening:
            try:
                with self.microphone as source:
                    # Listen for audio with timeout
                    audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=5)
                
                # Recognize speech
                command = self.recognizer.recognize_google(audio).lower()
                self.log_message(f"Heard: '{command}'")
                
                # Process the command
                self.process_command(command)
                
            except sr.WaitTimeoutError:
                # Normal timeout - continue listening
                pass
            except sr.UnknownValueError:
                self.log_message("Could not understand audio - please try again")
            except sr.RequestError as e:
                self.log_message(f"Speech recognition error: {str(e)}")
                break
            except Exception as e:
                self.log_message(f"Listening error: {str(e)}")
                logger.error(f"Listening error: {e}")
                break
    
    def process_manual_command(self, event=None):
        """Process manually typed command"""
        command = self.command_entry.get().strip()
        if command:
            self.log_message(f"Manual command: '{command}'")
            self.process_command(command.lower())
            self.command_entry.delete(0, tk.END)
    
    def process_command(self, command):
        """Process and execute voice or manual commands"""
        try:
            response = ""
            
            if "hello" in command or "hi" in command:
                response = "Hello! I'm your DESK-RUNNER-AI assistant. How can I help you?"
            
            elif "time" in command:
                current_time = datetime.now().strftime("%I:%M %p")
                response = f"The current time is {current_time}"
            
            elif "date" in command:
                current_date = datetime.now().strftime("%A, %B %d, %Y")
                response = f"Today is {current_date}"
            
            elif "help" in command:
                response = ("I can respond to commands like: hello, what time is it, "
                           "what date is it, help, status, or goodbye")
            
            elif "status" in command:
                response = "DESK-RUNNER-AI is running and ready to assist you"
            
            elif "goodbye" in command or "bye" in command:
                response = "Goodbye! Have a great day!"
            
            elif "stop listening" in command:
                response = "Stopping voice recognition"
                self.root.after(2000, self.stop_listening)  # Stop after speaking response
            
            else:
                response = f"I heard '{command}' but I'm not sure how to help with that yet. Try saying 'help' for available commands."
            
            self.log_message(f"Response: {response}")
            self.speak_response(response)
            
        except Exception as e:
            error_msg = f"Error processing command: {str(e)}"
            self.log_message(error_msg)
            logger.error(f"Command processing error: {e}")
    
    def speak_response(self, text):
        """Convert text to speech"""
        try:
            def speak():
                self.tts_engine.say(text)
                self.tts_engine.runAndWait()
            
            # Run TTS in separate thread to avoid blocking UI
            tts_thread = threading.Thread(target=speak, daemon=True)
            tts_thread.start()
            
        except Exception as e:
            self.log_message(f"Text-to-speech error: {str(e)}")
            logger.error(f"TTS error: {e}")
    
    def run(self):
        """Start the application"""
        try:
            self.log_message("Starting DESK-RUNNER-AI application...")
            self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
            self.root.mainloop()
        except Exception as e:
            logger.error(f"Application error: {e}")
            messagebox.showerror("Error", f"Application error: {str(e)}")
    
    def on_closing(self):
        """Handle application closing"""
        if self.is_listening:
            self.stop_listening()
        
        self.log_message("Shutting down DESK-RUNNER-AI...")
        self.root.destroy()

def main():
    """Main entry point"""
    try:
        app = DeskRunnerAI()
        app.run()
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        print(f"Fatal error: {e}")

if __name__ == "__main__":
    main()