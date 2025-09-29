"""Configuration management for RelayShell."""

import os
import yaml
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class LLMConfig:
    """Configuration for an LLM backend."""
    name: str
    provider: str  # openai, anthropic, google, etc.
    api_key: Optional[str] = None
    model: str = "gpt-3.5-turbo"
    endpoint: Optional[str] = None
    priority: int = 1
    enabled: bool = True
    timeout: int = 30
    max_tokens: int = 2048


@dataclass
class SpeechConfig:
    """Configuration for speech recognition and synthesis."""
    recognition_engine: str = "google"  # google, whisper, sphinx
    synthesis_engine: str = "pyttsx3"   # pyttsx3, gTTS, azure
    languages: List[str] = field(default_factory=lambda: ["en-US", "ta-IN"])
    default_language: str = "en-US"
    speech_rate: int = 200
    speech_volume: float = 0.9
    recognition_timeout: int = 5
    phrase_timeout: float = 1.0


@dataclass
class MonitoringConfig:
    """Configuration for clipboard and terminal monitoring."""
    clipboard_enabled: bool = True
    terminal_enabled: bool = True
    clipboard_poll_interval: float = 0.5
    terminal_keywords: List[str] = field(default_factory=lambda: [
        "error", "exception", "failed", "traceback", "syntax error"
    ])
    auto_trigger_keywords: List[str] = field(default_factory=lambda: [
        "fix this", "help with", "debug this"
    ])


@dataclass
class ServiceConfig:
    """Configuration for AI service management."""
    name: str
    command: str
    port: Optional[int] = None
    health_check_url: Optional[str] = None
    env_vars: Dict[str, str] = field(default_factory=dict)
    auto_start: bool = False
    restart_on_failure: bool = True


@dataclass
class Config:
    """Main configuration class for RelayShell."""
    
    # Core settings
    debug: bool = False
    log_level: str = "INFO"
    data_dir: str = "~/.relayshell"
    
    # Component configurations
    llm_configs: List[LLMConfig] = field(default_factory=list)
    speech_config: SpeechConfig = field(default_factory=SpeechConfig)
    monitoring_config: MonitoringConfig = field(default_factory=MonitoringConfig)
    services: List[ServiceConfig] = field(default_factory=list)
    
    # Editor integration
    editor_command: str = "code"  # VS Code by default
    test_command: str = "pytest"
    test_timeout: int = 60
    
    @classmethod
    def load_from_file(cls, config_path: str) -> 'Config':
        """Load configuration from YAML file."""
        path = Path(config_path).expanduser()
        
        if not path.exists():
            # Create default config
            config = cls.create_default()
            config.save_to_file(str(path))
            return config
            
        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            
        return cls.from_dict(data)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Config':
        """Create config from dictionary."""
        # Parse LLM configs
        llm_configs = []
        for llm_data in data.get('llm_configs', []):
            llm_configs.append(LLMConfig(**llm_data))
            
        # Parse services
        services = []
        for service_data in data.get('services', []):
            services.append(ServiceConfig(**service_data))
            
        # Parse speech config
        speech_data = data.get('speech_config', {})
        speech_config = SpeechConfig(**speech_data)
        
        # Parse monitoring config
        monitoring_data = data.get('monitoring_config', {})
        monitoring_config = MonitoringConfig(**monitoring_data)
        
        return cls(
            debug=data.get('debug', False),
            log_level=data.get('log_level', 'INFO'),
            data_dir=data.get('data_dir', '~/.relayshell'),
            llm_configs=llm_configs,
            speech_config=speech_config,
            monitoring_config=monitoring_config,
            services=services,
            editor_command=data.get('editor_command', 'code'),
            test_command=data.get('test_command', 'pytest'),
            test_timeout=data.get('test_timeout', 60)
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return {
            'debug': self.debug,
            'log_level': self.log_level,
            'data_dir': self.data_dir,
            'llm_configs': [self._llm_config_to_dict(llm) for llm in self.llm_configs],
            'speech_config': self._speech_config_to_dict(),
            'monitoring_config': self._monitoring_config_to_dict(),
            'services': [self._service_config_to_dict(svc) for svc in self.services],
            'editor_command': self.editor_command,
            'test_command': self.test_command,
            'test_timeout': self.test_timeout
        }
    
    def _llm_config_to_dict(self, llm: LLMConfig) -> Dict[str, Any]:
        """Convert LLM config to dict."""
        return {
            'name': llm.name,
            'provider': llm.provider,
            'api_key': llm.api_key,
            'model': llm.model,
            'endpoint': llm.endpoint,
            'priority': llm.priority,
            'enabled': llm.enabled,
            'timeout': llm.timeout,
            'max_tokens': llm.max_tokens
        }
    
    def _speech_config_to_dict(self) -> Dict[str, Any]:
        """Convert speech config to dict."""
        return {
            'recognition_engine': self.speech_config.recognition_engine,
            'synthesis_engine': self.speech_config.synthesis_engine,
            'languages': self.speech_config.languages,
            'default_language': self.speech_config.default_language,
            'speech_rate': self.speech_config.speech_rate,
            'speech_volume': self.speech_config.speech_volume,
            'recognition_timeout': self.speech_config.recognition_timeout,
            'phrase_timeout': self.speech_config.phrase_timeout
        }
    
    def _monitoring_config_to_dict(self) -> Dict[str, Any]:
        """Convert monitoring config to dict."""
        return {
            'clipboard_enabled': self.monitoring_config.clipboard_enabled,
            'terminal_enabled': self.monitoring_config.terminal_enabled,
            'clipboard_poll_interval': self.monitoring_config.clipboard_poll_interval,
            'terminal_keywords': self.monitoring_config.terminal_keywords,
            'auto_trigger_keywords': self.monitoring_config.auto_trigger_keywords
        }
    
    def _service_config_to_dict(self, service: ServiceConfig) -> Dict[str, Any]:
        """Convert service config to dict."""
        return {
            'name': service.name,
            'command': service.command,
            'port': service.port,
            'health_check_url': service.health_check_url,
            'env_vars': service.env_vars,
            'auto_start': service.auto_start,
            'restart_on_failure': service.restart_on_failure
        }
    
    def save_to_file(self, config_path: str) -> None:
        """Save configuration to YAML file."""
        path = Path(config_path).expanduser()
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'w', encoding='utf-8') as f:
            yaml.dump(self.to_dict(), f, default_flow_style=False, indent=2)
    
    @classmethod
    def create_default(cls) -> 'Config':
        """Create default configuration."""
        return cls(
            llm_configs=[
                LLMConfig(
                    name="gpt-4",
                    provider="openai",
                    model="gpt-4",
                    priority=1,
                    api_key=os.environ.get("OPENAI_API_KEY")
                ),
                LLMConfig(
                    name="claude",
                    provider="anthropic",
                    model="claude-3-sonnet-20240229",
                    priority=2,
                    api_key=os.environ.get("ANTHROPIC_API_KEY")
                ),
                LLMConfig(
                    name="gemini",
                    provider="google",
                    model="gemini-pro",
                    priority=3,
                    api_key=os.environ.get("GOOGLE_API_KEY")
                )
            ],
            services=[
                ServiceConfig(
                    name="local-llama",
                    command="ollama serve",
                    port=11434,
                    health_check_url="http://localhost:11434/api/tags",
                    auto_start=False
                )
            ]
        )