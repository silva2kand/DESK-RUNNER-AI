"""LLM Manager for parallel querying and response ranking."""

import asyncio
import logging
import time
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
import json

try:
    import openai
    import anthropic
    import google.generativeai as genai
    import requests
except ImportError as e:
    logging.warning(f"Some LLM dependencies not available: {e}")

from .config import LLMConfig


@dataclass
class LLMResponse:
    """Response from an LLM backend."""
    provider: str
    model: str
    response_text: str
    confidence_score: float
    response_time: float
    token_count: Optional[int] = None
    error: Optional[str] = None


class LLMManager:
    """Manages multiple LLM backends and parallel querying."""
    
    def __init__(self, llm_configs: List[LLMConfig]):
        self.configs = {config.name: config for config in llm_configs if config.enabled}
        self.logger = logging.getLogger(__name__)
        self.executor = ThreadPoolExecutor(max_workers=len(self.configs))
        
        # Initialize clients
        self.clients = {}
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialize LLM clients based on configuration."""
        for name, config in self.configs.items():
            try:
                if config.provider == "openai" and config.api_key:
                    self.clients[name] = openai.OpenAI(api_key=config.api_key)
                elif config.provider == "anthropic" and config.api_key:
                    self.clients[name] = anthropic.Anthropic(api_key=config.api_key)
                elif config.provider == "google" and config.api_key:
                    genai.configure(api_key=config.api_key)
                    self.clients[name] = genai.GenerativeModel(config.model)
                elif config.provider == "local" and config.endpoint:
                    # For local models like Ollama
                    self.clients[name] = {"endpoint": config.endpoint}
                
                self.logger.info(f"Initialized {config.provider} client: {name}")
                
            except Exception as e:
                self.logger.error(f"Failed to initialize {name}: {e}")
    
    async def query_parallel(self, prompt: str, context: Optional[str] = None) -> List[LLMResponse]:
        """Query all available LLMs in parallel."""
        tasks = []
        
        for name, config in self.configs.items():
            if name in self.clients:
                task = asyncio.create_task(
                    self._query_single_llm(name, config, prompt, context)
                )
                tasks.append(task)
        
        if not tasks:
            self.logger.warning("No LLM clients available")
            return []
        
        # Wait for all responses with timeout
        responses = []
        try:
            completed = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=max(config.timeout for config in self.configs.values())
            )
            
            for result in completed:
                if isinstance(result, LLMResponse):
                    responses.append(result)
                elif isinstance(result, Exception):
                    self.logger.error(f"LLM query failed: {result}")
                    
        except asyncio.TimeoutError:
            self.logger.warning("Some LLM queries timed out")
        
        return responses
    
    async def _query_single_llm(self, name: str, config: LLMConfig, 
                               prompt: str, context: Optional[str] = None) -> LLMResponse:
        """Query a single LLM backend."""
        start_time = time.time()
        
        try:
            # Prepare the prompt
            full_prompt = self._prepare_prompt(prompt, context)
            
            # Query based on provider
            if config.provider == "openai":
                response = await self._query_openai(name, config, full_prompt)
            elif config.provider == "anthropic":
                response = await self._query_anthropic(name, config, full_prompt)
            elif config.provider == "google":
                response = await self._query_google(name, config, full_prompt)
            elif config.provider == "local":
                response = await self._query_local(name, config, full_prompt)
            else:
                raise ValueError(f"Unsupported provider: {config.provider}")
            
            response_time = time.time() - start_time
            
            # Calculate confidence score
            confidence = self._calculate_confidence(response, config, response_time)
            
            return LLMResponse(
                provider=config.provider,
                model=config.model,
                response_text=response,
                confidence_score=confidence,
                response_time=response_time
            )
            
        except Exception as e:
            response_time = time.time() - start_time
            self.logger.error(f"Error querying {name}: {e}")
            
            return LLMResponse(
                provider=config.provider,
                model=config.model,
                response_text="",
                confidence_score=0.0,
                response_time=response_time,
                error=str(e)
            )
    
    def _prepare_prompt(self, prompt: str, context: Optional[str] = None) -> str:
        """Prepare the prompt with context and instructions."""
        system_prompt = """You are an AI assistant helping with code debugging and development.
        Provide clear, concise, and actionable solutions. If fixing code, provide the complete 
        corrected code snippet. Focus on practical solutions."""
        
        if context:
            full_prompt = f"{system_prompt}\n\nContext:\n{context}\n\nProblem:\n{prompt}\n\nSolution:"
        else:
            full_prompt = f"{system_prompt}\n\nProblem:\n{prompt}\n\nSolution:"
            
        return full_prompt
    
    async def _query_openai(self, name: str, config: LLMConfig, prompt: str) -> str:
        """Query OpenAI API."""
        client = self.clients[name]
        
        response = await asyncio.to_thread(
            client.chat.completions.create,
            model=config.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=config.max_tokens,
            timeout=config.timeout
        )
        
        return response.choices[0].message.content.strip()
    
    async def _query_anthropic(self, name: str, config: LLMConfig, prompt: str) -> str:
        """Query Anthropic API."""
        client = self.clients[name]
        
        response = await asyncio.to_thread(
            client.messages.create,
            model=config.model,
            max_tokens=config.max_tokens,
            messages=[{"role": "user", "content": prompt}],
            timeout=config.timeout
        )
        
        return response.content[0].text.strip()
    
    async def _query_google(self, name: str, config: LLMConfig, prompt: str) -> str:
        """Query Google Generative AI."""
        model = self.clients[name]
        
        response = await asyncio.to_thread(
            model.generate_content,
            prompt
        )
        
        return response.text.strip()
    
    async def _query_local(self, name: str, config: LLMConfig, prompt: str) -> str:
        """Query local LLM service (e.g., Ollama)."""
        endpoint = self.clients[name]["endpoint"]
        
        # Ollama API format
        data = {
            "model": config.model,
            "prompt": prompt,
            "stream": False
        }
        
        async with asyncio.timeout(config.timeout):
            response = await asyncio.to_thread(
                requests.post,
                f"{endpoint}/api/generate",
                json=data,
                timeout=config.timeout
            )
            response.raise_for_status()
            
            result = response.json()
            return result.get("response", "").strip()
    
    def _calculate_confidence(self, response: str, config: LLMConfig, 
                            response_time: float) -> float:
        """Calculate confidence score for the response."""
        confidence = 0.0
        
        # Base confidence from provider priority (higher priority = higher confidence)
        max_priority = max(cfg.priority for cfg in self.configs.values())
        confidence += (max_priority - config.priority + 1) / max_priority * 0.3
        
        # Response quality indicators
        if response:
            # Length factor (not too short, not too long)
            length_score = min(len(response) / 1000, 1.0) * 0.2
            confidence += length_score
            
            # Code quality indicators
            if "```" in response:  # Contains code blocks
                confidence += 0.2
            if any(keyword in response.lower() for keyword in ["fix", "solution", "corrected"]):
                confidence += 0.1
            if response.count('\n') > 3:  # Multi-line response
                confidence += 0.1
        
        # Response time factor (faster is better, but not too fast)
        if 1.0 <= response_time <= 10.0:
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def rank_responses(self, responses: List[LLMResponse]) -> List[LLMResponse]:
        """Rank responses by confidence score and other factors."""
        # Filter out error responses
        valid_responses = [r for r in responses if not r.error and r.response_text.strip()]
        
        if not valid_responses:
            return responses
        
        # Sort by confidence score (descending)
        ranked = sorted(valid_responses, key=lambda r: r.confidence_score, reverse=True)
        
        # Add error responses at the end
        error_responses = [r for r in responses if r.error or not r.response_text.strip()]
        ranked.extend(error_responses)
        
        return ranked
    
    async def get_best_response(self, prompt: str, context: Optional[str] = None) -> Optional[LLMResponse]:
        """Get the best response from all available LLMs."""
        responses = await self.query_parallel(prompt, context)
        
        if not responses:
            return None
        
        ranked_responses = self.rank_responses(responses)
        
        # Return the highest confidence response
        if ranked_responses and ranked_responses[0].confidence_score > 0:
            return ranked_responses[0]
        
        return None
    
    async def get_multiple_solutions(self, prompt: str, context: Optional[str] = None, 
                                   count: int = 3) -> List[LLMResponse]:
        """Get multiple ranked solutions from different LLMs."""
        responses = await self.query_parallel(prompt, context)
        ranked_responses = self.rank_responses(responses)
        
        return ranked_responses[:count]
    
    def get_status(self) -> Dict[str, Any]:
        """Get status of all LLM backends."""
        status = {}
        
        for name, config in self.configs.items():
            status[name] = {
                "provider": config.provider,
                "model": config.model,
                "enabled": config.enabled,
                "available": name in self.clients,
                "priority": config.priority
            }
        
        return status
    
    def shutdown(self):
        """Shutdown the LLM manager."""
        self.executor.shutdown(wait=True)
        self.logger.info("LLM Manager shutdown complete")