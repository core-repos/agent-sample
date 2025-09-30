"""
Anthropic (Claude) LLM provider implementation
"""
from typing import Optional
from langchain_anthropic import ChatAnthropic
from langchain.schema.language_model import BaseLanguageModel
from .base import LLMProvider
from config.settings import settings
import logging

logger = logging.getLogger(__name__)

class AnthropicProvider(LLMProvider):
    """Anthropic/Claude LLM provider"""
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.anthropic_api_key
        self.model = model or settings.anthropic_model
        
    def get_model(self, **kwargs) -> BaseLanguageModel:
        """Get Claude model instance"""
        if not self.validate_credentials():
            raise ValueError("Anthropic API key not configured")
        
        return ChatAnthropic(
            anthropic_api_key=self.api_key,
            model=self.model,
            temperature=kwargs.get("temperature", 0),
            max_tokens=kwargs.get("max_tokens", 4096),
            **kwargs
        )
    
    def validate_credentials(self) -> bool:
        """Check if Anthropic API key is configured"""
        return bool(self.api_key)
    
    @property
    def provider_name(self) -> str:
        return "anthropic"
    
    @property
    def model_name(self) -> str:
        return self.model