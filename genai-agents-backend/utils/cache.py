"""
Cache management utilities
"""
import json
import time
import hashlib
from typing import Any, Optional, Dict
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class CacheManager:
    """Simple cache manager for query results"""
    
    def __init__(self, cache_dir: str = "cache", ttl: int = 3600):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.ttl = ttl  # Time to live in seconds
        self.memory_cache: Dict[str, Any] = {}
        
    def _get_cache_key(self, query: str) -> str:
        """Generate cache key from query"""
        return hashlib.md5(query.lower().strip().encode()).hexdigest()
    
    def get(self, query: str) -> Optional[Dict[str, Any]]:
        """Get cached result for query"""
        cache_key = self._get_cache_key(query)
        
        # Check memory cache first
        if cache_key in self.memory_cache:
            cached = self.memory_cache[cache_key]
            if time.time() - cached["timestamp"] < self.ttl:
                return cached["data"]
        
        # Check file cache
        cache_file = self.cache_dir / f"{cache_key}.json"
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    cached = json.load(f)
                if time.time() - cached["timestamp"] < self.ttl:
                    # Update memory cache
                    self.memory_cache[cache_key] = cached
                    return cached["data"]
            except Exception as e:
                logger.error(f"Error reading cache: {e}")
        
        return None
    
    def set(self, query: str, data: Dict[str, Any]):
        """Cache query result"""
        cache_key = self._get_cache_key(query)
        
        cached = {
            "query": query,
            "data": data,
            "timestamp": time.time()
        }
        
        # Update memory cache
        self.memory_cache[cache_key] = cached
        
        # Write to file cache
        cache_file = self.cache_dir / f"{cache_key}.json"
        try:
            with open(cache_file, 'w') as f:
                json.dump(cached, f, indent=2)
        except Exception as e:
            logger.error(f"Error writing cache: {e}")
    
    def get_fallback(self, query: str) -> Optional[Dict[str, Any]]:
        """Get cached result ignoring TTL (for fallback)"""
        cache_key = self._get_cache_key(query)
        
        # Check memory cache
        if cache_key in self.memory_cache:
            return self.memory_cache[cache_key]["data"]
        
        # Check file cache
        cache_file = self.cache_dir / f"{cache_key}.json"
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    cached = json.load(f)
                return cached["data"]
            except Exception as e:
                logger.error(f"Error reading fallback cache: {e}")
        
        return None
    
    def clear(self):
        """Clear all cache"""
        self.memory_cache.clear()
        for cache_file in self.cache_dir.glob("*.json"):
            cache_file.unlink()
        logger.info("Cache cleared")