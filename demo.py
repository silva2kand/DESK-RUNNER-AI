#!/usr/bin/env python3
"""
Demo script for DESK-RUNNER-AI functionality
Shows how the command processing works without GUI
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def demo_command_processing():
    """Demonstrate command processing functionality"""
    print("DESK-RUNNER-AI Command Processing Demo")
    print("=" * 40)
    
    # Sample commands to test
    test_commands = [
        "hello",
        "what time is it",
        "what date is it", 
        "help",
        "status",
        "unknown command",
        "goodbye"
    ]
    
    print("Testing command processing with sample commands:\n")
    
    for command in test_commands:
        print(f"Command: '{command}'")
        response = process_demo_command(command)
        print(f"Response: {response}")
        print("-" * 30)

def process_demo_command(command):
    """Simulate command processing from the main application"""
    from datetime import datetime
    
    command = command.lower()
    
    if "hello" in command or "hi" in command:
        return "Hello! I'm your DESK-RUNNER-AI assistant. How can I help you?"
    
    elif "time" in command:
        current_time = datetime.now().strftime("%I:%M %p")
        return f"The current time is {current_time}"
    
    elif "date" in command:
        current_date = datetime.now().strftime("%A, %B %d, %Y")
        return f"Today is {current_date}"
    
    elif "help" in command:
        return ("I can respond to commands like: hello, what time is it, "
               "what date is it, help, status, or goodbye")
    
    elif "status" in command:
        return "DESK-RUNNER-AI is running and ready to assist you"
    
    elif "goodbye" in command or "bye" in command:
        return "Goodbye! Have a great day!"
    
    else:
        return f"I heard '{command}' but I'm not sure how to help with that yet. Try saying 'help' for available commands."

def show_features():
    """Show the features of DESK-RUNNER-AI"""
    print("\nDESK-RUNNER-AI Features:")
    print("=" * 30)
    features = [
        "✓ Voice Recognition - Real-time speech-to-text processing",
        "✓ Text-to-Speech - Audio responses using pyttsx3",
        "✓ GUI Interface - Clean interface built with tkinter",
        "✓ Manual Input - Alternative text-based command input",
        "✓ Activity Logging - Real-time activity log with timestamps",
        "✓ Threading - Non-blocking audio processing",
        "✓ Cross-platform - Works on Windows, macOS, and Linux"
    ]
    
    for feature in features:
        print(f"  {feature}")
    
    print("\nTo run the full GUI application:")
    print("  python main.py")
    print("\nTo run with the launcher script:")
    print("  ./run.sh")

if __name__ == "__main__":
    try:
        demo_command_processing()
        show_features()
        print("\nDemo completed successfully!")
    except Exception as e:
        print(f"Demo error: {e}")
        sys.exit(1)