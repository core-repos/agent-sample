"""
LLM Provider Factory - Creates appropriate LLM provider based on configuration
"""
from typing import Optional, Dict, Type
from .base import LLMProvider
from .anthropic_provider import AnthropicProvider
from .gemini_provider import GeminiProvider
from .openai_provider import OpenAIProvider
from .arctic_provider import ArcticProvider
from config.settings import settings
import logging

logger = logging.getLogger(__name__)

class LLMProviderFactory:
    """Factory for creating LLM provider instances"""
    
    _providers: Dict[str, Type[LLMProvider]] = {
        "anthropic": AnthropicProvider,
        "gemini": GeminiProvider,
        "openai": OpenAIProvider,
        "arctic": ArcticProvider,
    }
    
    @classmethod
    def register_provider(cls, name: str, provider_class: Type[LLMProvider]):
        """Register a new LLM provider"""
        cls._providers[name] = provider_class
        logger.info(f"Registered LLM provider: {name}")
    
    @classmethod
    def create_provider(
        cls, 
        provider_name: Optional[str] = None,
        **kwargs
    ) -> LLMProvider:
        """
        Create an LLM provider instance
        
        Args:
            provider_name: Name of the provider (anthropic, gemini, openai)
            **kwargs: Additional arguments for the provider
            
        Returns:
            LLMProvider instance
        """
        provider_name = provider_name or settings.default_llm_provider
        
        if provider_name not in cls._providers:
            raise ValueError(
                f"Unknown provider: {provider_name}. "
                f"Available providers: {list(cls._providers.keys())}"
            )
        
        provider_class = cls._providers[provider_name]
        provider = provider_class(**kwargs)
        
        if not provider.validate_credentials():
            logger.warning(f"Credentials not configured for {provider_name}")
            # Try fallback providers
            for fallback_name, fallback_class in cls._providers.items():
                if fallback_name != provider_name:
                    fallback = fallback_class()
                    if fallback.validate_credentials():
                        logger.info(f"Using fallback provider: {fallback_name}")
                        return fallback
            
            raise ValueError(f"No valid LLM provider credentials found")
        
        logger.info(f"Created LLM provider: {provider_name}")
        return provider
    
    @classmethod
    def get_available_providers(cls) -> list:
        """Get list of available providers with valid credentials"""
        available = []
        for name, provider_class in cls._providers.items():
            provider = provider_class()
            if provider.validate_credentials():
                available.append({
                    "name": name,
                    "model": provider.model_name
                })
        return available