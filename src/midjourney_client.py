import requests
import time
import logging
import base64
from io import BytesIO
from typing import Dict, Any, Optional
from .config import config

logger = logging.getLogger(__name__)

class StabilityAIClient:
    def __init__(self):
        self.api_key = config.STABILITY_AI_API_KEY
        self.api_url = "https://api.stability.ai/v2beta/stable-image/generate/ultra"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "image/*"
        }
    
    async def generate_image(self, prompt: str, request_id: str) -> Optional[bytes]:
        """
        Generate image using Stability AI API
        Returns the image bytes when generation is complete
        """
        try:
            logger.info(f"Starting image generation for request {request_id}: {prompt}")
            
            # Enhanced prompt for game assets
            enhanced_prompt = f"{prompt}, pixel art style, game asset, clean background, high quality, detailed"
            
            # Prepare form data for Stability AI (multipart/form-data)
            files = {
                "prompt": (None, enhanced_prompt),
                "output_format": (None, "png"),
                "aspect_ratio": (None, "1:1"),  # Square format for game assets
                "style_preset": (None, "pixel-art"),  # Use pixel art style
                "seed": (None, "0"),  # Random seed
                "cfg_scale": (None, "7"),  # Creativity vs adherence to prompt
                "clip_guidance_preset": (None, "FAST_BLUE"),
                "samples": (None, "1")
            }
            
            response = requests.post(
                self.api_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Accept": "image/*"  # Accept image response
                },
                files=files,  # This creates multipart/form-data
                timeout=60
            )
            
            if response.status_code == 200:
                logger.info(f"Image generation completed for request {request_id}")
                return response.content  # Return image bytes directly
            else:
                logger.error(f"Failed to generate image: {response.status_code} - {response.text}")
                return None
            
        except Exception as e:
            logger.error(f"Error generating image: {e}")
            return None
    
    def get_available_models(self) -> list:
        """Get available Stability AI models"""
        try:
            response = requests.get(
                "https://api.stability.ai/v1/engines/list",
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=10
            )
            if response.status_code == 200:
                engines = response.json()
                return [engine["id"] for engine in engines]
            return ["stable-diffusion-xl-1024-v1-0"]  # fallback
        except Exception as e:
            logger.error(f"Failed to fetch models: {e}")
            return ["stable-diffusion-xl-1024-v1-0"]
    
    def test_connection(self) -> bool:
        """Test Stability AI API connection"""
        try:
            response = requests.get(
                "https://api.stability.ai/v1/user/account",
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=10
            )
            if response.status_code == 200:
                balance = response.json()
                logger.info(f"Stability AI balance: ${balance.get('credits', 0):.2f}")
                return True
            return False
        except Exception as e:
            logger.error(f"API connection test failed: {e}")
            return False

# Alternative clients for different services
class LeonardoAIClient(StabilityAIClient):
    """Leonardo AI client - specialized for game assets"""
    
    def __init__(self):
        self.api_key = config.LEONARDO_AI_API_KEY
        self.api_url = "https://cloud.leonardo.ai/api/rest/v1/generations"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    async def generate_image(self, prompt: str, request_id: str) -> Optional[bytes]:
        logger.info(f"Leonardo AI: Generating image for request {request_id}")
        # Implementation for Leonardo AI would go here
        # For now, fallback to Stability AI
        return await super().generate_image(prompt, request_id)

class OpenAIDALLEClient(StabilityAIClient):
    """OpenAI DALL-E 3 client"""
    
    def __init__(self):
        self.api_key = config.OPENAI_API_KEY
        self.api_url = "https://api.openai.com/v1/images/generations"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    async def generate_image(self, prompt: str, request_id: str) -> Optional[bytes]:
        try:
            logger.info(f"DALL-E 3: Generating image for request {request_id}")
            
            data = {
                "model": "dall-e-3",
                "prompt": f"{prompt}, pixel art style, game asset",
                "size": "1024x1024",
                "quality": "hd",
                "n": 1,
                "response_format": "b64_json"
            }
            
            response = requests.post(self.api_url, headers=self.headers, json=data, timeout=60)
            
            if response.status_code == 200:
                result = response.json()
                image_b64 = result["data"][0]["b64_json"]
                return base64.b64decode(image_b64)
            else:
                logger.error(f"DALL-E API error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error with DALL-E generation: {e}")
            return None

# For development/testing
class MockImageClient:
    """Mock client for testing without actual API calls"""
    
    async def generate_image(self, prompt: str, request_id: str) -> Optional[bytes]:
        logger.info(f"MOCK: Generating image for '{prompt}' (request: {request_id})")
        # Simulate processing time
        time.sleep(2)
        
        # Create a simple colored square as mock image
        from PIL import Image
        import io
        
        img = Image.new('RGB', (512, 512), color='lightblue')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        return img_bytes.getvalue()
    
    def test_connection(self) -> bool:
        return True

# Client factory function
def create_image_client():
    """Create the appropriate image client based on configuration"""
    provider = config.IMAGE_PROVIDER.lower()
    
    if provider == "stability_ai":
        return StabilityAIClient()
    elif provider == "leonardo_ai":
        return LeonardoAIClient()
    elif provider == "openai_dalle":
        return OpenAIDALLEClient()
    elif provider == "mock":
        return MockImageClient()
    else:
        logger.warning(f"Unknown provider '{provider}', using Stability AI")
        return StabilityAIClient()

# Create the image client based on configuration
image_client = create_image_client()
logger.info(f"Using image generation provider: {config.IMAGE_PROVIDER}")
