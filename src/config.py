import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Redis Configuration
    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_USERNAME = os.getenv("REDIS_USERNAME", "")
    REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")
    
    # Redis Channels  
    GENERATION_REQUEST_CHANNEL = os.getenv("GENERATION_REQUEST_CHANNEL", "image_requests")
    GENERATION_COMPLETE_CHANNEL = os.getenv("COMPLETION_CHANNEL", "image_completions")
    
    # AWS S3 Configuration
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
    AWS_REGION = os.getenv("AWS_REGION", "us-west-2")
    S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "mobiarty-assets")
    
    # Image Generation API Configuration
    STABILITY_AI_API_KEY = os.getenv("STABILITY_AI_API_KEY")
    LEONARDO_AI_API_KEY = os.getenv("LEONARDO_AI_API_KEY")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    
    # Image Generation Provider (stability_ai, leonardo_ai, openai_dalle, mock)
    IMAGE_PROVIDER = os.getenv("IMAGE_PROVIDER", "stability_ai")
    
    # Go Backend Configuration
    GO_BACKEND_URL = os.getenv("GO_BACKEND_URL", "http://localhost:8080")
    
    # Image Processing Configuration
    MAX_IMAGE_SIZE = (1024, 1024)  # Max dimensions
    PIXEL_ART_SIZE = 64  # Target pixel art resolution
    
config = Config()
