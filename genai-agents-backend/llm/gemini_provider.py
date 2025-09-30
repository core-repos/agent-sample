"""
Google Gemini LLM provider implementation
"""
from typing import Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema.language_model import BaseLanguageModel
from .base import LLMProvider
from config.settings import settings
import logging

logger = logging.getLogger(__name__)

class GeminiProvider(LLMProvider):
    """Google Gemini LLM provider"""
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.gemini_api_key
        self.model = model or settings.gemini_model
        
    def get_model(self, **kwargs) -> BaseLanguageModel:
        """Get Gemini model instance"""
        if not self.validate_credentials():
            raise ValueError("Gemini API key not configured")
        
        return ChatGoogleGenerativeAI(
            google_api_key=self.api_key,
            model=self.model,
            temperature=kwargs.get("temperature", 0),
            **kwargs
        )
    
    def validate_credentials(self) -> bool:
        """Check if Gemini API key is configured"""
        return bool(self.api_key)
    
    @property
    def provider_name(self) -> str:
        return "gemini"
    
    @property
    def model_name(self) -> str:
        return self.model