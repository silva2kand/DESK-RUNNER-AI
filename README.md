# DESK-RUNNER-AI
DESKTOP LISTEN AND RUNNER AI

A Python-based desktop AI assistant that can listen to voice commands and execute various tasks through an intuitive GUI interface.

## Features

- **Voice Recognition**: Real-time speech-to-text processing using Google Speech Recognition
- **Text-to-Speech**: Audio responses using pyttsx3 engine
- **GUI Interface**: Clean, user-friendly interface built with tkinter
- **Manual Input**: Alternative text-based command input
- **Activity Logging**: Real-time activity log with timestamps
- **Threading**: Non-blocking audio processing for smooth user experience

## Requirements

- Python 3.7 or higher
- Microphone for voice input
- Internet connection for speech recognition
- Operating system: Windows, macOS, or Linux

## Installation

1. Clone the repository:
```bash
git clone https://github.com/silva2kand/DESK-RUNNER-AI.git
cd DESK-RUNNER-AI
```

2. Install required dependencies:
```bash
pip install -r requirements.txt
```

Note: On Linux, you may need to install additional packages:
```bash
sudo apt-get install python3-pyaudio
```

## Usage

1. Run the application:
```bash
python main.py
```

2. The GUI will open with the following interface:
   - **Status indicator**: Shows current state (Ready/Listening)
   - **Start/Stop Listening button**: Toggle voice recognition
   - **Activity Log**: Real-time log of all commands and responses
   - **Manual Command Input**: Type commands directly

3. **Voice Commands**: Click "Start Listening" and speak commands such as:
   - "Hello" or "Hi" - Get a greeting
   - "What time is it?" - Get current time
   - "What date is it?" - Get current date
   - "Help" - List available commands
   - "Status" - Check system status
   - "Stop listening" - Stop voice recognition
   - "Goodbye" or "Bye" - Exit greeting

4. **Manual Commands**: Type any of the above commands in the input field and press Enter

## Architecture

- **Main Application** (`main.py`): Core GUI and application logic
- **Speech Recognition**: Google Speech Recognition API integration
- **Text-to-Speech**: pyttsx3 for audio responses
- **Threading**: Separate threads for audio processing to maintain UI responsiveness
- **Logging**: Comprehensive logging for debugging and monitoring

## Troubleshooting

### Microphone Issues
- Ensure your microphone is properly connected and configured
- Check system microphone permissions
- Try adjusting microphone sensitivity in system settings

### Speech Recognition Issues
- Ensure stable internet connection (required for Google Speech Recognition)
- Speak clearly and at moderate pace
- Try manual command input as alternative

### Installation Issues
- Make sure Python 3.7+ is installed
- On Linux, install pyaudio system dependencies: `sudo apt-get install portaudio19-dev`
- On macOS, you may need: `brew install portaudio`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is open source. Please check the repository for specific license information.

## Future Enhancements

- [ ] Local speech recognition for offline usage
- [ ] Plugin system for custom commands
- [ ] Integration with system automation tools
- [ ] Command history and favorites
- [ ] Customizable voice and speech settings
- [ ] Multi-language support
- [ ] Advanced AI integration for natural language processing

## Support

For issues, questions, or contributions, please use the GitHub repository's issue tracker.
