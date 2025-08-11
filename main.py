#!/usr/bin/env python3
"""
Mobart - Generative Model Application
Consumes image generation requests from Redis pub/sub,
generates images via Midjourney API, and uploads to S3.
"""

import asyncio
import logging
import signal
import sys
from src.worker import worker

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    logger.info(f"Received signal {signum}, shutting down...")
    worker.stop()
    sys.exit(0)

def main():
    """Main entry point"""
    logger.info("🎨 Starting Mobart - Generative Model Application")
    
    # Setup signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Start the worker
        asyncio.run(worker.start())
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
