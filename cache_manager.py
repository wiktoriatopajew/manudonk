"""
Redis Cache Manager
Handles caching for frequently accessed data
"""
import redis
import json
import os
from typing import Optional, Any
from dotenv import load_dotenv

load_dotenv()

class CacheManager:
    def __init__(self):
        redis_url = os.getenv("REDIS_URL")
        
        if redis_url:
            try:
                self.redis_client = redis.from_url(
                    redis_url,
                    decode_responses=True,
                    socket_connect_timeout=2,
                    socket_timeout=2,
                    retry_on_timeout=True,
                    health_check_interval=30
                )
                # Test connection
                self.redis_client.ping()
                self.enabled = True
                print("✅ Redis cache connected successfully")
            except Exception as e:
                print(f"⚠️ Redis connection failed: {e}")
                print("⚠️ Falling back to no-cache mode")
                self.redis_client = None
                self.enabled = False
        else:
            print("ℹ️ Redis not configured (REDIS_URL not set) - cache disabled")
            self.redis_client = None
            self.enabled = False
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.enabled:
            return None
        
        try:
            value = self.redis_client.get(key)
            if value:
                return json.loads(value)
            return None
        except redis.exceptions.TimeoutError:
            print(f"⚠️ Redis timeout on get - disabling cache")
            self.enabled = False
            return None
        except Exception as e:
            print(f"Cache get error: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: int = 300):
        """
        Set value in cache
        ttl: Time to live in seconds (default 5 minutes)
        """
        if not self.enabled:
            return False
        
        try:
            serialized = json.dumps(value, default=str)
            self.redis_client.setex(key, ttl, serialized)
            return True
        except redis.exceptions.TimeoutError:
            print(f"⚠️ Redis timeout on set - disabling cache")
            self.enabled = False
            return False
        except Exception as e:
            print(f"Cache set error: {e}")
            return False
    
    def delete(self, key: str):
        """Delete key from cache"""
        if not self.enabled:
            return
        
        try:
            self.redis_client.delete(key)
        except Exception as e:
            print(f"Cache delete error: {e}")
    
    def clear_pattern(self, pattern: str):
        """Clear all keys matching pattern"""
        if not self.enabled:
            return
        
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                self.redis_client.delete(*keys)
        except Exception as e:
            print(f"Cache clear pattern error: {e}")
    
    def clear_all(self):
        """Clear entire cache"""
        if not self.enabled:
            return
        
        try:
            self.redis_client.flushdb()
        except Exception as e:
            print(f"Cache clear all error: {e}")

# Global cache instance
cache = CacheManager()
