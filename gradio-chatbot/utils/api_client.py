"""
API Client for backend communication
"""

import os
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import json
from typing import Dict, Any, Optional

# Configuration - Support both BACKEND_URL and API_BASE_URL env vars
BACKEND_BASE_URL = os.getenv('API_BASE_URL', os.getenv('BACKEND_URL', 'http://localhost:8010'))
BACKEND_URL = f"{BACKEND_BASE_URL}/api/bigquery/ask"
HEALTH_URL = f"{BACKEND_BASE_URL}/api/health"
EXAMPLES_URL = f"{BACKEND_BASE_URL}/api/examples"
MAX_RESPONSE_TIME = int(os.getenv('API_TIMEOUT', '60'))
MAX_RETRIES = 3

class APIClient:
    """Handle communication with the backend API with connection pooling and optimizations"""
    
    def __init__(self):
        self.session = requests.Session()
        
        # Configure connection pooling and keep-alive
        adapter = HTTPAdapter(
            pool_connections=10,
            pool_maxsize=20,
            max_retries=Retry(
                total=MAX_RETRIES,
                backoff_factor=0.3,
                status_forcelist=[429, 500, 502, 503, 504]
            )
        )
        
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        
        # Set default headers
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'BigQuery-Analytics-Agent/1.0'
        })
        
        # Set timeout
        self.timeout = MAX_RESPONSE_TIME
    
    def ask_question(self, question: str) -> Dict[str, Any]:
        """Send question to backend and get response"""
        
        if not question or not question.strip():
            return {
                'success': False,
                'error': 'Question cannot be empty',
                'data': None
            }
        
        # Clean question
        cleaned_question = question.strip()
        
        payload = {'question': cleaned_question}
        
        last_error = None
        
        # Try request with retries
        try:
            response = self.session.post(
                BACKEND_URL,
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'data': response.json(),
                    'error': None
                }
            else:
                error_text = response.text if hasattr(response, 'text') else 'Unknown error'
                last_error = f"API returned status {response.status_code}: {error_text}"
                
        except requests.exceptions.Timeout:
            last_error = f"Request timed out after {self.timeout} seconds"
        except requests.exceptions.ConnectionError:
            last_error = "Could not connect to backend API"
        except Exception as e:
            last_error = str(e)
        
        # Return error response
        return {
            'success': False,
            'error': last_error or "Unknown error occurred",
            'data': None
        }
    
    def check_health(self) -> bool:
        """Check if backend API is healthy"""
        try:
            response = self.session.get(HEALTH_URL, timeout=5)
            return response.status_code == 200
        except Exception:
            return False
    
    def get_examples(self) -> Optional[list]:
        """Get example queries from backend"""
        try:
            response = self.session.get(EXAMPLES_URL, timeout=5)
            if response.status_code == 200:
                examples = response.json().get('examples', [])
                return [example for example in examples if example]
        except Exception:
            pass
        return None

# Create singleton instance
api_client = APIClient()