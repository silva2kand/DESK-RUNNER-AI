"""Basic tests for RelayShell components."""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock

from relayshell.config import Config, LLMConfig, SpeechConfig
from relayshell.llm_manager import LLMManager, LLMResponse


class TestConfig:
    """Test configuration management."""
    
    def test_default_config_creation(self):
        """Test creating default configuration."""
        config = Config.create_default()
        
        assert config.debug is False
        assert config.log_level == "INFO"
        assert len(config.llm_configs) >= 3  # Should have at least 3 LLM configs
        assert config.speech_config.default_language == "en-US"
    
    def test_config_serialization(self):
        """Test config to/from dict conversion."""
        config = Config.create_default()
        config_dict = config.to_dict()
        
        # Should be able to recreate from dict
        recreated = Config.from_dict(config_dict)
        
        assert recreated.debug == config.debug
        assert recreated.log_level == config.log_level
        assert len(recreated.llm_configs) == len(config.llm_configs)


class TestLLMManager:
    """Test LLM manager functionality."""
    
    @pytest.fixture
    def llm_configs(self):
        """Create test LLM configurations."""
        return [
            LLMConfig(
                name="test-gpt",
                provider="openai",
                model="gpt-3.5-turbo",
                api_key="test-key",
                priority=1
            ),
            LLMConfig(
                name="test-claude",
                provider="anthropic", 
                model="claude-3-haiku",
                api_key="test-key",
                priority=2
            )
        ]
    
    def test_llm_manager_initialization(self, llm_configs):
        """Test LLM manager initialization."""
        manager = LLMManager(llm_configs)
        
        assert len(manager.configs) == 2
        assert "test-gpt" in manager.configs
        assert "test-claude" in manager.configs
    
    def test_confidence_calculation(self, llm_configs):
        """Test confidence score calculation."""
        manager = LLMManager(llm_configs)
        
        # Test with good response
        config = llm_configs[0]
        confidence = manager._calculate_confidence(
            response="Here's a complete solution with code:\n```python\nprint('hello')\n```",
            config=config,
            response_time=2.0
        )
        
        assert 0.0 <= confidence <= 1.0
        assert confidence > 0.5  # Should be reasonably high for good response
    
    def test_response_ranking(self, llm_configs):
        """Test response ranking by confidence."""
        manager = LLMManager(llm_configs)
        
        responses = [
            LLMResponse(
                provider="openai",
                model="gpt-4",
                response_text="Simple answer",
                confidence_score=0.3,
                response_time=1.0
            ),
            LLMResponse(
                provider="anthropic",
                model="claude-3",
                response_text="Detailed solution with code:\n```python\nfix_code()\n```",
                confidence_score=0.8,
                response_time=2.0
            ),
            LLMResponse(
                provider="google",
                model="gemini",
                response_text="",
                confidence_score=0.0,
                response_time=5.0,
                error="API Error"
            )
        ]
        
        ranked = manager.rank_responses(responses)
        
        # Should be ranked by confidence (highest first)
        assert ranked[0].confidence_score == 0.8
        assert ranked[1].confidence_score == 0.3
        # Error response should be last
        assert ranked[2].error is not None


@pytest.mark.asyncio
class TestAsyncComponents:
    """Test async components."""
    
    async def test_mock_llm_query(self):
        """Test mocked LLM query."""
        configs = [
            LLMConfig(
                name="mock-llm",
                provider="test",
                model="test-model",
                api_key="test"
            )
        ]
        
        manager = LLMManager(configs)
        
        # Mock the query method
        with patch.object(manager, '_query_single_llm', new_callable=AsyncMock) as mock_query:
            mock_query.return_value = LLMResponse(
                provider="test",
                model="test-model", 
                response_text="Mock response",
                confidence_score=0.9,
                response_time=1.0
            )
            
            responses = await manager.query_parallel("test prompt")
            
            assert len(responses) == 1
            assert responses[0].response_text == "Mock response"
            assert responses[0].confidence_score == 0.9


def test_extract_code_blocks():
    """Test code block extraction from AI responses."""
    from relayshell.core import RelayShell
    
    # Create minimal RelayShell instance for testing
    relay = RelayShell()
    
    text_with_code = '''
    Here's the solution:
    
    ```python
    def fix_error():
        return "fixed"
    ```
    
    And another block:
    
    ```javascript
    console.log("hello");
    ```
    '''
    
    code_blocks = relay._extract_code_blocks(text_with_code)
    
    assert len(code_blocks) == 2
    assert 'def fix_error():' in code_blocks[0]
    assert 'console.log("hello");' in code_blocks[1]


if __name__ == "__main__":
    pytest.main([__file__])