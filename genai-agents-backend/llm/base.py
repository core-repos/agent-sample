"""
Base LLM provider interface
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from langchain.schema.language_model import BaseLanguageModel

class LLMProvider(ABC):
    """Abstract base class for LLM providers"""
    
    @abstractmethod
    def get_model(self, **kwargs) -> BaseLanguageModel:
        """Get the LLM model instance"""
        pass
    
    @abstractmethod
    def validate_credentials(self) -> bool:
        """Validate if credentials are properly configured"""
        pass
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the provider name"""
        pass
    
    @property
    @abstractmethod
    def model_name(self) -> str:
        """Return the model name"""
        pass