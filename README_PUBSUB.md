# Mobart - Redis Pub/Sub Generative Model

A Python application that consumes image generation requests via Redis pub/sub, generates images using Midjourney API, post-processes them for game assets, and uploads to S3.

## Architecture Overview

```
Go Backend --[Redis Pub/Sub]--> Python Mobart App --[Midjourney API]--> Image Generation
     ^                                    |                                      |
     |                                    |                                      v
     +<--[Completion Notification]--------+<--[S3 Upload]<--[Post Processing]<--+
```

## Features

- ✅ **Redis Pub/Sub Consumer** - Listens for image generation requests
- ✅ **Midjourney API Integration** - Generates images via API
- ✅ **S3 Upload** - Stores processed images in AWS S3
- ✅ **Post-Processing Pipeline** - Optimizes images for game assets
- ✅ **Completion Notifications** - Notifies Go backend when done
- ✅ **Docker Support** - Easy deployment and scaling
- ✅ **Comprehensive Logging** - Full request/response tracking
- ✅ **Health Checks** - Startup validation of all services

## Quick Start

### 1. Environment Setup

Create a `.env` file:
```bash
# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=

# AWS S3 Configuration  
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-west-2
S3_BUCKET_NAME=mobiarty-assets

# Midjourney API Configuration
MIDJOURNEY_API_KEY=your_midjourney_api_key
MIDJOURNEY_API_URL=https://api.midjourneyapi.xyz/mj/v2

# Go Backend Configuration
GO_BACKEND_URL=http://localhost:8080
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run with Docker

```bash
# Start Redis and the worker
docker-compose up --build
```

### 4. Run Locally (Development)

```bash
# Start Redis first
docker run -d -p 6379:6379 redis:7-alpine

# Run the Python app
python main.py
```

## Message Format

### Generation Request (Go → Python)
Channel: `image_generation_requests`
```json
{
  "request_id": "uuid-string",
  "user_id": "user-uuid", 
  "prompt": "A fierce dragon with glowing eyes"
}
```

### Completion Notification (Python → Go)
Channel: `image_generation_complete`
```json
{
  "request_id": "uuid-string",
  "user_id": "user-uuid",
  "status": "completed",
  "s3_key": "generated/user-id/request-id.png",
  "s3_url": "https://mobiarty-assets.s3.us-west-2.amazonaws.com/...",
  "generation_time_seconds": 45.2,
  "timestamp": "2025-08-10T19:30:00"
}
```

### Error Notification
```json
{
  "request_id": "uuid-string", 
  "user_id": "user-uuid",
  "status": "failed",
  "error": "Image generation failed",
  "timestamp": "2025-08-10T19:30:00"
}
```

## Integration with Go Backend

### 1. Go Backend Publishes Request
```go
// In your Go backend
func PublishImageRequest(requestID, userID, prompt string) {
    message := map[string]string{
        "request_id": requestID,
        "user_id": userID, 
        "prompt": prompt,
    }
    
    jsonData, _ := json.Marshal(message)
    redisClient.Publish("image_generation_requests", jsonData)
}
```

### 2. Go Backend Subscribes to Completions
```go
// Subscribe to completion notifications
pubsub := redisClient.Subscribe("image_generation_complete")

for msg := range pubsub.Channel() {
    var completion CompletionMessage
    json.Unmarshal([]byte(msg.Payload), &completion)
    
    // Update database with S3 URL
    updateGeneratedContent(completion.RequestID, completion.S3URL)
}
```

## Configuration

### Redis Channels
- **Input**: `image_generation_requests` 
- **Output**: `image_generation_complete`

### Image Processing
- **Max Size**: 1024x1024px
- **Format**: PNG with RGBA
- **Optimization**: Enabled
- **Cache**: 1 year S3 cache headers

### S3 Storage Structure
```
mobiarty-assets/
└── generated/
    └── {user_id}/
        └── {request_id}.png
```

## Development Notes

### Midjourney API
The current implementation uses a placeholder Midjourney API. Replace with:
- Official Midjourney API (when available)
- Unofficial Midjourney services
- Alternative image generation APIs (DALL-E, Stable Diffusion, etc.)

### Post-Processing
The `_apply_pixel_art_processing()` function is currently a placeholder. Integrate your existing pixel art logic here.

### Testing
Use the provided test script to simulate the full workflow:
```bash
python test_workflow.py
```

## Monitoring

### Logs
- **File**: `mobart.log`
- **Console**: Real-time output
- **Docker**: `docker-compose logs mobart`

### Health Checks
The app performs startup health checks for:
- Redis connection
- S3 bucket access  
- Midjourney API availability

## Scaling

To handle more requests:
1. **Multiple Workers**: Run multiple instances of the app
2. **Redis Clustering**: Scale Redis for high throughput
3. **S3 Optimization**: Use S3 Transfer Acceleration
4. **Async Processing**: Current implementation is already async

## Error Handling

- **Retry Logic**: Built into Midjourney polling
- **Graceful Degradation**: Continues on non-critical errors
- **Comprehensive Logging**: Full error stack traces
- **Status Notifications**: Always notifies Go backend of outcomes
