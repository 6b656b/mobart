import boto3
import logging
import requests
from PIL import Image
from io import BytesIO
from typing import Optional
from botocore.exceptions import ClientError, NoCredentialsError
from .config import config

logger = logging.getLogger(__name__)

class S3Uploader:
    def __init__(self):
        try:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=config.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY,
                region_name=config.AWS_REGION
            )
            self.bucket_name = config.S3_BUCKET_NAME
        except NoCredentialsError:
            logger.error("AWS credentials not found")
            self.s3_client = None
    
    async def upload_image_bytes(self, image_bytes: bytes, s3_key: str) -> Optional[str]:
        """
        Process image bytes and upload to S3
        Returns the S3 URL if successful
        """
        if not self.s3_client:
            logger.error("S3 client not initialized")
            return None
        
        try:
            # Step 1: Load and process image from bytes
            logger.info(f"Processing image bytes for upload to: {s3_key}")
            image = Image.open(BytesIO(image_bytes))
            processed_image = self._process_image(image)
            
            # Step 2: Convert to bytes for upload
            img_buffer = BytesIO()
            processed_image.save(img_buffer, format='PNG', optimize=True)
            img_buffer.seek(0)
            
            # Step 3: Upload to S3
            logger.info(f"Uploading to S3: {s3_key}")
            self.s3_client.upload_fileobj(
                img_buffer,
                self.bucket_name,
                s3_key,
                ExtraArgs={
                    'ContentType': 'image/png',
                    'CacheControl': 'max-age=31536000',  # 1 year cache
                }
            )
            
            # Return the S3 URL
            s3_url = f"https://{self.bucket_name}.s3.{config.AWS_REGION}.amazonaws.com/{s3_key}"
            logger.info(f"Successfully uploaded to: {s3_url}")
            return s3_url
            
        except ClientError as e:
            logger.error(f"S3 upload error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error uploading image: {e}")
            return None

    async def download_and_upload_image(self, image_url: str, s3_key: str) -> Optional[str]:
        """
        Download image from URL, process it, and upload to S3
        Returns the S3 URL if successful
        """
        if not self.s3_client:
            logger.error("S3 client not initialized")
            return None
        
        try:
            # Step 1: Download image from URL
            logger.info(f"Downloading image from: {image_url}")
            response = requests.get(image_url, timeout=30)
            if response.status_code != 200:
                logger.error(f"Failed to download image: {response.status_code}")
                return None
            
            # Step 2: Load and process image
            image = Image.open(BytesIO(response.content))
            processed_image = self._process_image(image)
            
            # Step 3: Convert to bytes for upload
            img_buffer = BytesIO()
            processed_image.save(img_buffer, format='PNG', optimize=True)
            img_buffer.seek(0)
            
            # Step 4: Upload to S3
            logger.info(f"Uploading to S3: {s3_key}")
            self.s3_client.upload_fileobj(
                img_buffer,
                self.bucket_name,
                s3_key,
                ExtraArgs={
                    'ContentType': 'image/png',
                    'CacheControl': 'max-age=31536000',  # 1 year cache
                }
            )
            
            # Return the S3 URL
            s3_url = f"https://{self.bucket_name}.s3.{config.AWS_REGION}.amazonaws.com/{s3_key}"
            logger.info(f"Successfully uploaded to: {s3_url}")
            return s3_url
            
        except ClientError as e:
            logger.error(f"S3 upload error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error uploading image: {e}")
            return None
    
    def _process_image(self, image: Image.Image) -> Image.Image:
        """
        Post-process the generated image to meet game asset standards
        """
        try:
            # Convert to RGBA if not already
            if image.mode != 'RGBA':
                image = image.convert('RGBA')
            
            # Resize if larger than max size
            if image.size[0] > config.MAX_IMAGE_SIZE[0] or image.size[1] > config.MAX_IMAGE_SIZE[1]:
                image.thumbnail(config.MAX_IMAGE_SIZE, Image.Resampling.LANCZOS)
                logger.info(f"Resized image to: {image.size}")
            
            # Apply pixel art processing (placeholder for now)
            processed_image = self._apply_pixel_art_processing(image)
            
            return processed_image
            
        except Exception as e:
            logger.error(f"Error processing image: {e}")
            return image  # Return original if processing fails
    
    def _apply_pixel_art_processing(self, image: Image.Image) -> Image.Image:
        """
        Apply pixel art post-processing
        This is a placeholder function - implement your specific processing logic here
        """
        # TODO: Implement pixel art processing
        # This could include:
        # - Color palette reduction
        # - Pixel art scaling algorithms
        # - Dithering
        # - Sprite sheet generation
        # - Asset optimization
        
        logger.info("Applying pixel art post-processing (placeholder)")
        
        # For now, just return the original image
        # You can integrate your existing pyxelate logic here
        return image
    
    def test_connection(self) -> bool:
        """Test S3 connection"""
        if not self.s3_client:
            return False
        
        try:
            # Try to list objects in bucket (just to test connection)
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            return True
        except Exception as e:
            logger.error(f"S3 connection test failed: {e}")
            return False

s3_uploader = S3Uploader()
