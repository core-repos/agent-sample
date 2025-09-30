"""
Arctic-Text2SQL-R1 Local LLM Provider
Runs Arctic-Text2SQL-R1 model locally for SQL generation
"""
import os
import logging
from typing import Optional, Dict, Any
import requests
from langchain.llms.base import LLM
from langchain.callbacks.manager import CallbackManagerForLLMRun
from .base import LLMProvider

logger = logging.getLogger(__name__)

class ArcticText2SQLLLM(LLM):
    """Custom LangChain LLM wrapper for Arctic-Text2SQL-R1"""
    
    base_url: str = "http://localhost:11434"  # Ollama default
    model_name: str = "sqlcoder:7b"
    temperature: float = 0.1
    max_tokens: int = 2048
    
    @property
    def _llm_type(self) -> str:
        return "arctic-text2sql"
    
    def _call(
        self,
        prompt: str,
        stop: Optional[list] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        """Call the Arctic model via Ollama API"""
        try:
            # Check if this is a SQL-related query
            if "SELECT" in prompt.upper() or "cost_analysis" in prompt.lower() or "application" in prompt.lower():
                # If it already contains SQL, just pass it through
                enhanced_prompt = prompt
            else:
                # For natural language queries, enhance for SQL generation
                enhanced_prompt = f"""Generate a BigQuery SQL query for: {prompt}
                
Use the table: cost_analysis
Columns: date, cto, cloud, tr_product_pillar_team, tr_subpillar_name, tr_product_id, tr_product, application, service_name, managed_service, environment, cost

SQL:"""
            
            # Ollama API endpoint
            url = f"{self.base_url}/api/generate"
            
            # Prepare the request with lower timeout for faster response
            payload = {
                "model": self.model_name,
                "prompt": enhanced_prompt,
                "temperature": 0.1,
                "max_tokens": 500,
                "stream": False
            }
            
            if stop:
                payload["stop"] = stop
            
            # Make the request with shorter timeout
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            return result.get("response", "")
            
        except requests.exceptions.ConnectionError:
            logger.error(f"Failed to connect to Ollama at {self.base_url}")
            raise ValueError(
                f"Cannot connect to Ollama at {self.base_url}. "
                "Please ensure Ollama is running with Arctic-Text2SQL model. "
                "Run: ollama pull snowflake/arctic-text2sql"
            )
        except Exception as e:
            logger.error(f"Error calling Arctic model: {e}")
            raise

class ArcticProvider(LLMProvider):
    """Arctic-Text2SQL-R1 Local LLM Provider"""
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        model_name: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 2048,
        **kwargs
    ):
        self.base_url = base_url or os.getenv("ARCTIC_BASE_URL", "http://localhost:11434")
        self._model_name = model_name or os.getenv("ARCTIC_MODEL_NAME", "sqlcoder:7b")
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.additional_params = kwargs
    
    def get_model(self, **kwargs) -> ArcticText2SQLLLM:
        """Get Arctic-Text2SQL model instance"""
        params = {
            "base_url": self.base_url,
            "model_name": self._model_name,
            "temperature": kwargs.get("temperature", self.temperature),
            "max_tokens": kwargs.get("max_tokens", self.max_tokens),
        }
        params.update(self.additional_params)
        params.update(kwargs)
        
        return ArcticText2SQLLLM(**params)
    
    def validate_credentials(self) -> bool:
        """Check if Ollama is running with Arctic model"""
        try:
            # Check if Ollama is running
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code != 200:
                return False
            
            # Check if SQL model is available
            models = response.json().get("models", [])
            for model in models:
                model_name = model.get("name", "").lower()
                if "sqlcoder" in model_name or "arctic" in model_name or \
                   "text2sql" in model_name or "codellama" in model_name:
                    logger.info(f"Found SQL model: {model.get('name')}")
                    self._model_name = model.get("name", "sqlcoder:7b")  # Use actual model name
                    return True
            
            logger.warning("SQL generation model not found in Ollama")
            return False
            
        except Exception as e:
            logger.debug(f"Arctic validation failed: {e}")
            return False
    
    @property
    def provider_name(self) -> str:
        return "arctic"
    
    @property
    def model_name(self) -> str:
        return self._model_name