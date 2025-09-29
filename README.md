# RelayShell - AI-Powered Development Assistant

**RelayShell** is a comprehensive AI-powered development assistant that provides:

- 🗣️ **Tamil/English Speech I/O** - Listen and speak in both languages
- 📋 **Smart Monitoring** - Clipboard and terminal output capture  
- 🤖 **Multi-LLM Parallel Querying** - Query multiple AI backends simultaneously
- 🎯 **Auto-Fix Selection** - Automatically pick the best solution
- ⚡ **Editor Integration** - Paste fixes and run tests automatically
- 🚀 **AI Service Management** - Deploy and manage AI services via YAML

## 🌟 Features

### Speech Recognition & Synthesis
- **Multilingual Support**: Tamil (ta-IN) and English (en-US)
- **Voice Commands**: Control RelayShell with speech
- **Auto Language Detection**: Seamlessly switch between languages
- **Text-to-Speech**: Get responses in your preferred language

### Intelligent Monitoring
- **Clipboard Watching**: Detects when you copy error messages or code
- **Terminal Monitoring**: Watches for errors in running processes
- **File Monitoring**: Track log files for error patterns
- **Auto-Triggering**: Automatically responds to error keywords

### Multi-LLM Backend Support
- **OpenAI GPT Models** (GPT-4, GPT-3.5)
- **Anthropic Claude** (Claude-3 Sonnet, Haiku)
- **Google Gemini** (Gemini Pro)
- **Local Models** (Ollama, Text Generation WebUI)
- **Parallel Querying**: Get multiple solutions simultaneously
- **Smart Ranking**: Automatically select the best response

### Code Assistance
- **Error Analysis**: Understand and fix code errors
- **Code Generation**: Generate code snippets and solutions
- **Test Integration**: Automatically run tests after applying fixes
- **Editor Integration**: Works with VS Code, vim, emacs, and more

### AI Service Management
- **YAML-Based Configuration**: Define services declaratively
- **Health Monitoring**: Automatic health checks and restarts
- **Port Management**: Avoid conflicts with automatic port allocation
- **Environment Configuration**: Set environment variables per service

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/silva2kand/DESK-RUNNER-AI.git
cd DESK-RUNNER-AI

# Install dependencies
pip install -e .

# Initialize configuration
relayshell init --example
```

### Configuration

Edit `~/.relayshell/config.yaml` and add your API keys:

```yaml
llm_configs:
  - name: gpt-4
    provider: openai
    api_key: "your_openai_api_key_here"
    
  - name: claude
    provider: anthropic
    api_key: "your_anthropic_api_key_here"
```

### Basic Usage

```bash
# Start RelayShell
relayshell start

# Query LLMs directly
relayshell query "How to fix a Python import error?"

# Check status
relayshell status

# Set language
relayshell set-language ta-IN
```

## 🎮 Usage Examples

### Voice Commands
- **"Fix this error"** - Analyze clipboard content for errors
- **"Help with debugging"** - Get debugging assistance
- **"Switch to Tamil"** - Change language to Tamil
- **"Run tests"** - Execute test suite

### Error Handling Workflow
1. **Copy error message** to clipboard
2. **RelayShell detects** the error automatically
3. **Multiple AI models** analyze the problem
4. **Best solution selected** and presented
5. **Apply fix** with voice confirmation
6. **Tests run** automatically to verify

### Service Management
```bash
# Deploy services from YAML
relayshell service deploy config/services.yaml

# Start specific service
relayshell service start ollama-llama2

# List all services
relayshell service list

# Stop service
relayshell service stop ollama-llama2
```

## 📁 Project Structure

```
relayshell/
├── __init__.py          # Package initialization
├── core.py              # Main RelayShell orchestrator
├── config.py            # Configuration management
├── speech_handler.py    # Speech recognition/synthesis
├── llm_manager.py       # Multi-LLM backend management
├── monitoring.py        # Clipboard/terminal monitoring
├── service_manager.py   # AI service lifecycle management
└── cli.py              # Command-line interface

config/
├── default.yaml         # Default configuration
└── services.yaml        # Example service definitions
```

## ⚙️ Configuration

### Speech Configuration
```yaml
speech_config:
  recognition_engine: google    # google, whisper, sphinx
  synthesis_engine: pyttsx3     # pyttsx3, gTTS, azure
  languages: [en-US, ta-IN]
  default_language: en-US
  speech_rate: 200
  speech_volume: 0.9
```

### LLM Configuration
```yaml
llm_configs:
  - name: gpt-4
    provider: openai
    model: gpt-4
    api_key: your_key
    priority: 1              # Lower = higher priority
    timeout: 30
    max_tokens: 2048
```

### Monitoring Configuration
```yaml
monitoring_config:
  clipboard_enabled: true
  terminal_enabled: true
  auto_trigger_keywords:
    - "fix this"
    - "help with"
    - "debug this"
  terminal_keywords:
    - "error"
    - "exception"
    - "failed"
```

## 🔧 Advanced Features

### Custom AI Services
Create `services.yaml`:
```yaml
services:
  - name: my-local-llm
    command: python run_model.py
    port: 8080
    health_check_url: http://localhost:8080/health
    env_vars:
      MODEL_PATH: ./models/my-model
    auto_start: true
    restart_on_failure: true
```

### Tamil Language Support
RelayShell includes comprehensive Tamil support:
- **Speech Recognition**: Understands Tamil voice commands
- **Text-to-Speech**: Responds in Tamil
- **Translation**: Auto-translates between Tamil and English
- **Code Comments**: Can generate Tamil code comments

### Editor Integration
Supported editors:
- **VS Code**: `editor_command: code`
- **Vim**: `editor_command: vim`
- **Emacs**: `editor_command: emacs`
- **Sublime**: `editor_command: subl`

## 🔍 Monitoring & Debugging

### Status Checking
```bash
relayshell status
```

Shows:
- Speech recognition status
- Available LLM backends
- Monitoring components
- Running AI services
- Conversation history

### Logs
Logs are stored in `~/.relayshell/logs/`:
- `relayshell.log` - Main application logs
- Service logs available via `relayshell service logs <name>`

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Submit a pull request

### Development Setup
```bash
# Install development dependencies
pip install -e .[dev]

# Run tests
pytest

# Code formatting
black relayshell/
flake8 relayshell/
```

## 📜 License

MIT License - see LICENSE file for details.

## 🙏 Acknowledgments

- OpenAI for GPT models
- Anthropic for Claude models  
- Google for Gemini and speech services
- The open-source AI community

## 🆘 Support

- **Issues**: Report bugs on GitHub Issues
- **Discussions**: Join GitHub Discussions
- **Documentation**: Check the wiki for detailed guides

---

**RelayShell** - Making AI development assistance accessible in Tamil and English! 🚀
