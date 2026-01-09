# intelligence/service/app/loaders/base_loader.py
"""Base loader with common functionality."""

from typing import Dict, Any, Optional
import structlog

logger = structlog.get_logger()


class BaseLoader:
    """Base loader with caching and error handling."""
    
    def __init__(self, cache_enabled: bool = True):
        """Initialize base loader.
        
        Args:
            cache_enabled: Whether to cache loaded configurations
        """
        self.cache_enabled = cache_enabled
        self._cache: Dict[str, Any] = {}
    
    def _get_cached(self, key: str) -> Optional[Any]:
        """Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None
        """
        if self.cache_enabled and key in self._cache:
            logger.debug("cache_hit", key=key)
            return self._cache[key]
        return None
    
    def _set_cache(self, key: str, value: Any) -> None:
        """Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
        """
        if self.cache_enabled:
            self._cache[key] = value
    
    def clear_cache(self) -> None:
        """Clear all cached values."""
        self._cache.clear()
        logger.info("cache_cleared")
