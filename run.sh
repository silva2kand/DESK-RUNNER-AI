#!/bin/bash
# Launcher script for DESK-RUNNER-AI

echo "Starting DESK-RUNNER-AI..."
echo "Desktop Listen and Runner AI"
echo "=========================="

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed or not in PATH"
    echo "Please install Python 3.7 or higher"
    exit 1
fi

# Check if required packages are installed
echo "Checking dependencies..."
python3 -c "import speech_recognition, pyttsx3, tkinter" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Installing required dependencies..."
    pip3 install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "Error: Failed to install dependencies"
        echo "Please run: pip3 install -r requirements.txt"
        exit 1
    fi
fi

echo "Starting application..."
python3 main.py

echo "DESK-RUNNER-AI has been closed."