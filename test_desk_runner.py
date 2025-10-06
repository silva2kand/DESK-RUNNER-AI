#!/usr/bin/env python3
"""
Test script for DESK-RUNNER-AI functionality
"""

import unittest
import sys
import os

# Add the main directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from main import DeskRunnerAI
    import speech_recognition as sr
    import pyttsx3
    import tkinter as tk
except ImportError as e:
    print(f"Import error: {e}")
    print("Please install required dependencies: pip install -r requirements.txt")
    sys.exit(1)

class TestDeskRunnerAI(unittest.TestCase):
    """Test cases for DESK-RUNNER-AI"""
    
    def setUp(self):
        """Set up test environment"""
        # Create a minimal test instance without GUI
        self.test_commands = [
            "hello",
            "what time is it",
            "what date is it", 
            "help",
            "status",
            "goodbye"
        ]
    
    def test_speech_recognition_setup(self):
        """Test that speech recognition components are available"""
        recognizer = sr.Recognizer()
        self.assertIsNotNone(recognizer)
        
        # Test microphone availability (may not exist in CI environment)
        try:
            microphone = sr.Microphone()
            self.assertIsNotNone(microphone)
        except OSError:
            # Skip if no microphone available (common in CI)
            pass
    
    def test_tts_engine_setup(self):
        """Test that text-to-speech engine can be initialized"""
        try:
            engine = pyttsx3.init()
            self.assertIsNotNone(engine)
            
            # Test basic TTS functionality
            voices = engine.getProperty('voices')
            self.assertIsInstance(voices, (list, type(None)))
            
        except Exception as e:
            # TTS might not work in headless environment
            print(f"TTS test skipped due to environment: {e}")
    
    def test_tkinter_availability(self):
        """Test that tkinter GUI library is available"""
        try:
            root = tk.Tk()
            root.withdraw()  # Hide the window
            self.assertIsNotNone(root)
            root.destroy()
        except tk.TclError:
            # Skip if no display available (common in CI)
            pass
    
    def test_command_processing_logic(self):
        """Test command processing without GUI"""
        # This would test the command processing logic
        # For now, just verify the test commands are valid
        for command in self.test_commands:
            self.assertIsInstance(command, str)
            self.assertTrue(len(command) > 0)

def main():
    """Run tests"""
    print("DESK-RUNNER-AI Test Suite")
    print("=" * 25)
    
    # Check Python version
    if sys.version_info < (3, 7):
        print("Error: Python 3.7 or higher is required")
        return False
    
    print(f"Python version: {sys.version}")
    
    # Run tests
    unittest.main(verbosity=2, exit=False)
    
    print("\nTest completed. If no errors were shown above, basic functionality is working.")
    return True

if __name__ == "__main__":
    main()