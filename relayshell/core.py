"""Core RelayShell class that orchestrates all components."""

import asyncio
import logging
import os
import subprocess
import tempfile
import time
from typing import Optional, Dict, Any, List
from pathlib import Path

from .config import Config
from .speech_handler import SpeechHandler
from .llm_manager import LLMManager, LLMResponse
from .monitoring import MonitorManager, MonitorEvent
from .service_manager import ServiceManager


class RelayShell:
    """Main RelayShell class that coordinates all components."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize RelayShell with configuration."""
        # Load configuration
        if config_path is None:
            config_path = os.path.expanduser("~/.relayshell/config.yaml")
        
        self.config = Config.load_from_file(config_path)
        
        # Setup logging
        self._setup_logging()
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.speech_handler = SpeechHandler(self.config.speech_config)
        self.llm_manager = LLMManager(self.config.llm_configs)
        self.monitor_manager = MonitorManager(self.config.monitoring_config)
        self.service_manager = ServiceManager(self.config.services)
        
        # State
        self.is_running = False
        self.current_context = ""
        self.conversation_history = []
        
        # Setup callbacks
        self._setup_callbacks()
        
        self.logger.info("RelayShell initialized successfully")
    
    def _setup_logging(self):
        """Setup logging configuration."""
        # Create logs directory
        logs_dir = Path(self.config.data_dir).expanduser() / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup console handler (with color if available)
        console_handler = logging.StreamHandler()
        try:
            import colorlog
            console_handler.setFormatter(colorlog.ColoredFormatter(
                '%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            ))
        except ImportError:
            # Fallback to basic formatter if colorlog not available
            console_handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            ))
        
        # Setup file handler
        file_handler = logging.FileHandler(logs_dir / "relayshell.log")
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        ))
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, self.config.log_level.upper()))
        root_logger.addHandler(console_handler)
        root_logger.addHandler(file_handler)
        
        # Reduce noise from external libraries
        logging.getLogger('requests').setLevel(logging.WARNING)
        logging.getLogger('urllib3').setLevel(logging.WARNING)
    
    def _setup_callbacks(self):
        """Setup callbacks between components."""
        # Speech recognition callback
        self.speech_handler.on_speech_recognized = self._handle_speech_input
        self.speech_handler.on_speech_error = self._handle_speech_error
        
        # Monitoring callbacks
        self.monitor_manager.on_monitor_event = self._handle_monitor_event
    
    async def start(self):
        """Start RelayShell and all components."""
        if self.is_running:
            self.logger.warning("RelayShell is already running")
            return
        
        try:
            self.logger.info("Starting RelayShell...")
            
            # Start services first
            await self.service_manager.start_all_auto_services()
            
            # Start monitoring
            self.monitor_manager.start()
            
            # Start speech recognition
            if self.speech_handler.start_listening():
                self.logger.info("Speech recognition started")
            else:
                self.logger.warning("Speech recognition failed to start")
            
            self.is_running = True
            
            # Announce startup
            await self.speak("RelayShell AI assistant is now active and listening")
            
            self.logger.info("RelayShell started successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to start RelayShell: {e}")
            await self.stop()
            raise
    
    async def stop(self):
        """Stop RelayShell and all components."""
        if not self.is_running:
            return
        
        try:
            self.logger.info("Stopping RelayShell...")
            
            # Announce shutdown
            await self.speak("RelayShell is shutting down")
            
            # Stop components
            self.speech_handler.stop_listening()
            self.monitor_manager.stop()
            await self.service_manager.stop_all_services()
            self.llm_manager.shutdown()
            
            self.is_running = False
            self.logger.info("RelayShell stopped")
            
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")
    
    async def speak(self, text: str, language: Optional[str] = None):
        """Speak text using TTS."""
        self.logger.info(f"Speaking: {text}")
        self.speech_handler.speak(text, language)
    
    async def _handle_speech_input(self, text: str, language: str):
        """Handle speech input from user."""
        self.logger.info(f"Speech input ({language}): {text}")
        
        # Add to conversation history
        self.conversation_history.append({
            "type": "speech",
            "content": text,
            "language": language,
            "timestamp": time.time()
        })
        
        # Process the speech command
        await self._process_user_input(text, "speech", {"language": language})
    
    def _handle_speech_error(self, error: str):
        """Handle speech recognition errors."""
        self.logger.warning(f"Speech error: {error}")
    
    async def _handle_monitor_event(self, event: MonitorEvent):
        """Handle events from monitoring system."""
        self.logger.info(f"Monitor event from {event.source}: {event.content[:100]}...")
        
        # Check if this needs AI assistance
        if self._needs_ai_assistance(event):
            await self._process_user_input(
                event.content, 
                event.source, 
                event.metadata
            )
    
    def _needs_ai_assistance(self, event: MonitorEvent) -> bool:
        """Determine if an event needs AI assistance."""
        content_lower = event.content.lower()
        
        # Check for explicit help requests
        help_keywords = ["fix this", "help with", "debug this", "solve this"]
        if any(keyword in content_lower for keyword in help_keywords):
            return True
        
        # Check for error patterns
        error_keywords = ["error", "exception", "failed", "traceback", "syntax error"]
        if any(keyword in content_lower for keyword in error_keywords):
            return True
        
        return False
    
    async def _process_user_input(self, content: str, source: str, metadata: Dict[str, Any]):
        """Process user input and generate AI response."""
        try:
            self.logger.info(f"Processing input from {source}")
            
            # Prepare context
            context = self._prepare_context(source, metadata)
            
            # Get AI response
            response = await self.llm_manager.get_best_response(content, context)
            
            if response and response.response_text:
                await self._handle_ai_response(response, content, source)
            else:
                await self.speak("I'm sorry, I couldn't get a response from the AI services.")
                
        except Exception as e:
            self.logger.error(f"Error processing input: {e}")
            await self.speak("I encountered an error while processing your request.")
    
    def _prepare_context(self, source: str, metadata: Dict[str, Any]) -> str:
        """Prepare context for AI query."""
        context_parts = []
        
        # Add source information
        context_parts.append(f"Input source: {source}")
        
        # Add metadata
        if metadata:
            context_parts.append(f"Metadata: {metadata}")
        
        # Add recent conversation history
        if self.conversation_history:
            recent_history = self.conversation_history[-3:]  # Last 3 interactions
            history_text = "\n".join([
                f"- {item['type']}: {item['content'][:100]}..."
                for item in recent_history
            ])
            context_parts.append(f"Recent conversation:\n{history_text}")
        
        # Add current working directory and environment info
        context_parts.append(f"Working directory: {os.getcwd()}")
        
        return "\n\n".join(context_parts)
    
    async def _handle_ai_response(self, response: LLMResponse, original_input: str, source: str):
        """Handle AI response and take appropriate actions."""
        self.logger.info(f"AI response from {response.provider}: {response.response_text[:100]}...")
        
        # Speak the response
        await self.speak(f"I found a solution using {response.provider}")
        
        # Check if response contains code
        if "```" in response.response_text:
            await self._handle_code_response(response, original_input)
        else:
            # Just speak the response
            await self.speak(response.response_text)
        
        # Add to conversation history
        self.conversation_history.append({
            "type": "ai_response",
            "content": response.response_text,
            "provider": response.provider,
            "confidence": response.confidence_score,
            "timestamp": time.time()
        })
    
    async def _handle_code_response(self, response: LLMResponse, original_input: str):
        """Handle AI response containing code."""
        # Extract code blocks
        code_blocks = self._extract_code_blocks(response.response_text)
        
        if not code_blocks:
            await self.speak(response.response_text)
            return
        
        # Ask if user wants to apply the fix
        await self.speak("I found a code solution. Should I apply it to your editor?")
        
        # Listen for confirmation
        confirmation = await self.speech_handler.listen_once(timeout=10.0)
        
        if confirmation and ("yes" in confirmation.lower() or "apply" in confirmation.lower()):
            await self._apply_code_fix(code_blocks[0])  # Apply first code block
        else:
            await self.speak("I'll just show you the solution then.")
            await self.speak(response.response_text)
    
    def _extract_code_blocks(self, text: str) -> List[str]:
        """Extract code blocks from AI response."""
        import re
        
        # Find code blocks marked with ```
        pattern = r"```(?:\w+)?\n(.*?)\n```"
        matches = re.findall(pattern, text, re.DOTALL)
        
        return [match.strip() for match in matches]
    
    async def _apply_code_fix(self, code: str):
        """Apply code fix to editor."""
        try:
            # Create temporary file with the code
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            # Open in editor
            editor_cmd = self.config.editor_command
            subprocess.Popen([editor_cmd, temp_file])
            
            await self.speak("I've opened the solution in your editor")
            
            # Optionally run tests
            if self.config.test_command:
                await self.speak("Should I run tests to verify the fix?")
                
                test_confirmation = await self.speech_handler.listen_once(timeout=10.0)
                if test_confirmation and "yes" in test_confirmation.lower():
                    await self._run_tests()
            
        except Exception as e:
            self.logger.error(f"Failed to apply code fix: {e}")
            await self.speak("I couldn't apply the fix to your editor")
    
    async def _run_tests(self):
        """Run tests to verify code fix."""
        try:
            await self.speak("Running tests...")
            
            # Run test command
            result = subprocess.run(
                self.config.test_command.split(),
                capture_output=True,
                text=True,
                timeout=self.config.test_timeout
            )
            
            if result.returncode == 0:
                await self.speak("Tests passed successfully!")
            else:
                await self.speak("Tests failed. Let me analyze the errors.")
                
                # Get AI help for test failures
                error_context = f"Test command: {self.config.test_command}\nOutput: {result.stdout}\nErrors: {result.stderr}"
                await self._process_user_input(
                    "Tests failed, please help fix the issues",
                    "test_failure",
                    {"test_output": error_context}
                )
                
        except subprocess.TimeoutExpired:
            await self.speak("Tests timed out")
        except Exception as e:
            self.logger.error(f"Test execution failed: {e}")
            await self.speak("I couldn't run the tests")
    
    # Command interface methods
    async def process_command(self, command: str) -> str:
        """Process a text command and return response."""
        await self._process_user_input(command, "command", {})
        return "Command processed"
    
    def get_status(self) -> Dict[str, Any]:
        """Get status of all RelayShell components."""
        return {
            "running": self.is_running,
            "speech": {
                "listening": self.speech_handler.is_listening,
                "current_language": self.speech_handler.current_language,
                "available_languages": self.speech_handler.get_available_languages()
            },
            "llm": self.llm_manager.get_status(),
            "monitoring": self.monitor_manager.get_status(),
            "services": self.service_manager.get_all_status(),
            "conversation_history_length": len(self.conversation_history)
        }
    
    def switch_language(self, language: str):
        """Switch the primary language for speech I/O."""
        self.speech_handler.set_language(language)
        self.logger.info(f"Language switched to: {language}")
    
    async def deploy_services(self, yaml_path: str) -> bool:
        """Deploy services from YAML configuration."""
        return await self.service_manager.deploy_from_yaml(yaml_path)
    
    def save_config(self, config_path: Optional[str] = None):
        """Save current configuration."""
        if config_path is None:
            config_path = os.path.expanduser("~/.relayshell/config.yaml")
        
        self.config.save_to_file(config_path)
        self.logger.info(f"Configuration saved to {config_path}")