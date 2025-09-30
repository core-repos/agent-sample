"""
OpenAI LLM provider implementation
"""
from typing import Optional
from langchain_openai import ChatOpenAI
from langchain.schema.language_model import BaseLanguageModel
from .base import LLMProvider
from config.settings import settings
import logging

logger = logging.getLogger(__name__)

class OpenAIProvider(LLMProvider):
    """OpenAI GPT LLM provider"""
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.openai_api_key
        self.model = model or settings.openai_model
        
    def get_model(self, **kwargs) -> BaseLanguageModel:
        """Get OpenAI model instance"""
        if not self.validate_credentials():
            raise ValueError("OpenAI API key not configured")
        
        return ChatOpenAI(
            openai_api_key=self.api_key,
            model_name=self.model,
            temperature=kwargs.get("temperature", 0),
            **kwargs
        )
    
    def validate_credentials(self) -> bool:
        """Check if OpenAI API key is configured"""
        return bool(self.api_key)
    
    @property
    def provider_name(self) -> str:
        return "openai"
    
    @property
    def model_name(self) -> str:
        return self.model