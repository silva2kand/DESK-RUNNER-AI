"""RelayShell - AI-powered development assistant with multilingual support."""

__version__ = "1.0.0"
__author__ = "RelayShell Team"

from .core import RelayShell
from .config import Config
from .llm_manager import LLMManager
from .speech_handler import SpeechHandler

__all__ = ["RelayShell", "Config", "LLMManager", "SpeechHandler"]