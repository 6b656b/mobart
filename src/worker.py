import asyncio
import json
import logging
import uuid
import requests
from datetime import datetime
from typing import Dict, Any

from .redis_client import redis_client
from .midjourney_client import image_client
from .s3_uploader import s3_uploader
from .config import config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('mobart.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class ImageGenerationWorker:
    def __init__(self):
        self.running = False
    
    async def start(self):
        """Start the worker to consume generation requests"""
        self.running = True
        logger.info("Starting Image Generation Worker...")
        
        # Health checks
        if not self._health_checks():
            logger.error("Health checks failed, stopping worker")
            return
        
        # Subscribe to Redis pub/sub
        pubsub = redis_client.subscribe_to_requests()
        
        logger.info(f"Listening for requests on channel: {config.GENERATION_REQUEST_CHANNEL}")
        
        try:
            for message in pubsub.listen():
                if not self.running:
                    break
                
                if message['type'] == 'message':
                    await self._process_message(message['data'])
                    
        except KeyboardInterrupt:
            logger.info("Received interrupt signal, shutting down...")
        except Exception as e:
            logger.error(f"Unexpected error in worker: {e}")
        finally:
            self.stop()
    
    async def _process_message(self, message_data: str):
        """Process a single generation request message"""
        try:
            # Parse the message
            request = json.loads(message_data)
            request_id = request.get('request_id')
            user_id = request.get('user_id')
            prompt = request.get('prompt')
            
            if not all([request_id, user_id, prompt]):
                logger.error(f"Invalid request format: {request}")
                return
            
            logger.info(f"Processing request {request_id} for user {user_id}: {prompt}")
            
            # Generate the image
            success = await self._generate_and_upload_image(request_id, user_id, prompt)
            
            if success:
                logger.info(f"Successfully completed request {request_id}")
            else:
                logger.error(f"Failed to complete request {request_id}")
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse message JSON: {e}")
        except Exception as e:
            logger.error(f"Error processing message: {e}")
    
    async def _generate_and_upload_image(self, request_id: str, user_id: str, prompt: str) -> bool:
        """Generate image, upload to S3, and notify completion"""
        try:
            start_time = datetime.now()
            
            # Step 1: Generate image using AI API
            logger.info(f"Starting image generation for request {request_id}")
            image_bytes = await image_client.generate_image(prompt, request_id)
            
            if not image_bytes:
                logger.error(f"Failed to generate image for request {request_id}")
                self._notify_failure(request_id, user_id, "Image generation failed")
                return False
            
            # Step 2: Upload to S3
            s3_key = f"generated/{user_id}/{request_id}.png"
            s3_url = await s3_uploader.upload_image_bytes(image_bytes, s3_key)
            
            if not s3_url:
                logger.error(f"Failed to upload image to S3 for request {request_id}")
                self._notify_failure(request_id, user_id, "S3 upload failed")
                return False
            
            # Step 3: Notify completion
            generation_time = (datetime.now() - start_time).total_seconds()
            self._notify_success(request_id, user_id, s3_key, s3_url, generation_time)
            
            return True
            
        except Exception as e:
            logger.error(f"Unexpected error in generation pipeline: {e}")
            self._notify_failure(request_id, user_id, f"Unexpected error: {str(e)}")
            return False
    
    def _notify_success(self, request_id: str, user_id: str, s3_key: str, s3_url: str, generation_time: float):
        """Notify Go backend of successful completion via HTTP API"""
        try:
            # We'll let the Go backend generate signed URLs when needed
            # Just provide the S3 key for now
            payload = {
                "request_id": request_id,
                "status": "completed",
                "content_url": s3_key  # Store S3 key, Go backend will generate signed URLs on demand
            }
            
            response = requests.post(
                f"{config.GO_BACKEND_URL}/api/internal/update_status",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                logger.info(f"✅ Successfully notified Go backend for request {request_id}")
            else:
                logger.error(f"❌ Failed to notify Go backend: {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.error(f"❌ Error notifying success to Go backend: {e}")
    
    def _notify_failure(self, request_id: str, user_id: str, error_message: str):
        """Notify Go backend of failure via HTTP API"""
        try:
            payload = {
                "request_id": request_id,
                "status": "failed",
                "content_url": ""
            }
            
            response = requests.post(
                f"{config.GO_BACKEND_URL}/api/internal/update_status",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                logger.info(f"✅ Successfully notified Go backend of failure for request {request_id}")
            else:
                logger.error(f"❌ Failed to notify Go backend of failure: {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.error(f"❌ Error notifying failure to Go backend: {e}")
            
        logger.error(f"Request {request_id} failed: {error_message}")
    
    def _health_checks(self) -> bool:
        """Perform startup health checks"""
        logger.info("Performing health checks...")
        
        # Check Redis connection
        if not redis_client.health_check():
            logger.error("Redis health check failed")
            return False
        logger.info("✓ Redis connection OK")
        
        # Check S3 connection
        if not s3_uploader.test_connection():
            logger.error("S3 health check failed")
            return False
        logger.info("✓ S3 connection OK")
        
        # Check Image Generation API (optional - might fail in dev)
        if image_client.test_connection():
            logger.info("✓ Image Generation API connection OK")
        else:
            logger.warning("⚠ Image Generation API connection failed (continuing anyway)")
        
        logger.info("Health checks completed")
        return True
    
    def stop(self):
        """Stop the worker gracefully"""
        logger.info("Stopping Image Generation Worker...")
        self.running = False

# Create global worker instance
worker = ImageGenerationWorker()
