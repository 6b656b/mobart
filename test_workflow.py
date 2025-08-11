#!/usr/bin/env python3
"""
Test script to simulate the complete workflow:
1. Publish a generation request to Redis
2. Monitor completion notifications
3. Verify the full pipeline works
"""

import redis
import json
import uuid
import time
import threading
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WorkflowTester:
    def __init__(self):
        self.redis_client = redis.Redis(
            host='localhost',
            port=6379,
            decode_responses=True
        )
        self.results = {}
        
    def test_complete_workflow(self):
        """Test the complete generation workflow"""
        logger.info("🧪 Starting workflow test...")
        
        # Start listening for completions in a separate thread
        completion_thread = threading.Thread(target=self._monitor_completions)
        completion_thread.daemon = True
        completion_thread.start()
        
        # Generate test requests
        test_requests = [
            {
                "request_id": str(uuid.uuid4()),
                "user_id": str(uuid.uuid4()),
                "prompt": "A fierce dragon with glowing eyes, pixel art style"
            },
            {
                "request_id": str(uuid.uuid4()),
                "user_id": str(uuid.uuid4()),
                "prompt": "A tiny fairy with sparkling wings, game asset"
            }
        ]
        
        # Publish requests
        for request in test_requests:
            self._publish_request(request)
            self.results[request["request_id"]] = {
                "sent_at": datetime.now(),
                "status": "pending"
            }
        
        # Wait for results
        logger.info("⏳ Waiting for completions...")
        timeout = 300  # 5 minutes
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            pending = [rid for rid, result in self.results.items() if result["status"] == "pending"]
            if not pending:
                logger.info("✅ All requests completed!")
                break
            
            logger.info(f"📋 Still waiting for {len(pending)} requests...")
            time.sleep(10)
        
        # Print results
        self._print_results()
    
    def _publish_request(self, request):
        """Publish a generation request"""
        try:
            message = json.dumps(request)
            self.redis_client.publish("image_generation_requests", message)
            logger.info(f"📤 Published request {request['request_id']}: {request['prompt'][:50]}...")
        except Exception as e:
            logger.error(f"❌ Failed to publish request: {e}")
    
    def _monitor_completions(self):
        """Monitor completion notifications"""
        try:
            pubsub = self.redis_client.pubsub()
            pubsub.subscribe("image_generation_complete")
            logger.info("👂 Listening for completion notifications...")
            
            for message in pubsub.listen():
                if message['type'] == 'message':
                    try:
                        completion = json.loads(message['data'])
                        request_id = completion.get('request_id')
                        
                        if request_id in self.results:
                            self.results[request_id].update({
                                "status": completion.get('status'),
                                "completed_at": datetime.now(),
                                "s3_url": completion.get('s3_url'),
                                "error": completion.get('error'),
                                "generation_time": completion.get('generation_time_seconds')
                            })
                            
                            status = completion.get('status')
                            if status == 'completed':
                                logger.info(f"✅ Request {request_id} completed successfully")
                            else:
                                logger.error(f"❌ Request {request_id} failed: {completion.get('error')}")
                    
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse completion message: {e}")
                        
        except Exception as e:
            logger.error(f"Error monitoring completions: {e}")
    
    def _print_results(self):
        """Print test results summary"""
        logger.info("\n" + "="*60)
        logger.info("📊 WORKFLOW TEST RESULTS")
        logger.info("="*60)
        
        total = len(self.results)
        completed = len([r for r in self.results.values() if r["status"] == "completed"])
        failed = len([r for r in self.results.values() if r["status"] == "failed"])
        pending = len([r for r in self.results.values() if r["status"] == "pending"])
        
        logger.info(f"📈 Total Requests: {total}")
        logger.info(f"✅ Completed: {completed}")
        logger.info(f"❌ Failed: {failed}")
        logger.info(f"⏳ Pending: {pending}")
        
        for request_id, result in self.results.items():
            logger.info(f"\n🔍 Request: {request_id[:8]}...")
            logger.info(f"   Status: {result['status']}")
            
            if result["status"] == "completed":
                duration = (result["completed_at"] - result["sent_at"]).total_seconds()
                logger.info(f"   Duration: {duration:.1f}s")
                logger.info(f"   Generation Time: {result.get('generation_time', 'N/A')}s")
                logger.info(f"   S3 URL: {result.get('s3_url', 'N/A')}")
            elif result["status"] == "failed":
                logger.info(f"   Error: {result.get('error', 'Unknown error')}")
        
        logger.info("="*60)

def test_redis_connection():
    """Test basic Redis connection"""
    try:
        r = redis.Redis(host='localhost', port=6379, decode_responses=True)
        r.ping()
        logger.info("✅ Redis connection OK")
        return True
    except Exception as e:
        logger.error(f"❌ Redis connection failed: {e}")
        return False

if __name__ == "__main__":
    print("🎨 Mobart Workflow Tester")
    print("This script tests the complete Redis pub/sub workflow")
    print()
    
    # Test Redis connection first
    if not test_redis_connection():
        print("Please start Redis first: docker run -d -p 6379:6379 redis:7-alpine")
        exit(1)
    
    # Run the workflow test
    tester = WorkflowTester()
    tester.test_complete_workflow()
