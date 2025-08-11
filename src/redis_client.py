import redis
import json
import logging
from typing import Dict, Any
from .config import config

logger = logging.getLogger(__name__)

class RedisClient:
    def __init__(self):
        self.redis_client = redis.Redis(
            host=config.REDIS_HOST,
            port=config.REDIS_PORT,
            username=config.REDIS_USERNAME if config.REDIS_USERNAME else None,
            password=config.REDIS_PASSWORD if config.REDIS_PASSWORD else None,
            decode_responses=True
        )
        
    def subscribe_to_requests(self):
        """Subscribe to image generation requests"""
        pubsub = self.redis_client.pubsub()
        pubsub.subscribe(config.GENERATION_REQUEST_CHANNEL)
        logger.info(f"Subscribed to {config.GENERATION_REQUEST_CHANNEL}")
        return pubsub
    
    def publish_completion(self, message: Dict[str, Any]):
        """Publish completion notification"""
        try:
            self.redis_client.publish(
                config.GENERATION_COMPLETE_CHANNEL,
                json.dumps(message)
            )
            logger.info(f"Published completion: {message}")
        except Exception as e:
            logger.error(f"Failed to publish completion: {e}")
    
    def health_check(self) -> bool:
        """Check Redis connection health"""
        try:
            self.redis_client.ping()
            return True
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return False

redis_client = RedisClient()
