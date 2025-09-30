"""
Application configuration and settings
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Application
    app_name: str = "BigQuery Analytics Agent"
    app_version: str = "1.0.0"
    debug: bool = Field(default=False, env="DEBUG")
    
    # BigQuery Configuration (REQUIRED - no defaults for security)
    gcp_project_id: str = Field(env="GCP_PROJECT_ID", description="Google Cloud Project ID")
    bq_dataset: str = Field(env="BQ_DATASET", description="BigQuery Dataset name")
    gcp_service_account_key: Optional[str] = Field(default=None, env="GOOGLE_APPLICATION_CREDENTIALS")
    
    # LLM Configuration
    anthropic_api_key: Optional[str] = Field(default=None, env="ANTHROPIC_API_KEY")
    gemini_api_key: Optional[str] = Field(default=None, env="GEMINI_API_KEY")
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    
    # Arctic Local LLM Configuration
    arctic_base_url: str = Field(default="http://localhost:11434", env="ARCTIC_BASE_URL")
    arctic_model_name: str = Field(default="arctic-text2sql", env="ARCTIC_MODEL_NAME")
    
    # Default LLM provider
    default_llm_provider: str = Field(default="anthropic", env="DEFAULT_LLM_PROVIDER")
    llm_provider: str = Field(default="anthropic", env="LLM_PROVIDER")
    
    # Model configurations
    anthropic_model: str = Field(default="claude-3-5-sonnet-20241022", env="ANTHROPIC_MODEL")
    gemini_model: str = Field(default="gemini-pro", env="GEMINI_MODEL")
    openai_model: str = Field(default="gpt-4", env="OPENAI_MODEL")
    arctic_model: str = Field(default="arctic-text2sql", env="ARCTIC_MODEL")
    
    # API Configuration
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8010, env="API_PORT")
    cors_origins: list = Field(default=["*"], env="CORS_ORIGINS")
    
    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_dir: str = Field(default="logs", env="LOG_DIR")
    
    # Cache Configuration
    enable_cache: bool = Field(default=True, env="ENABLE_CACHE")
    cache_ttl: int = Field(default=3600, env="CACHE_TTL")
    
    # Agent Configuration
    agent_max_iterations: int = Field(default=50, env="AGENT_MAX_ITERATIONS")
    agent_max_execution_time: float = Field(default=120.0, env="AGENT_MAX_EXECUTION_TIME")
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields from backend_config.py

# Singleton instance
settings = Settings()