# 🎨 Image Generation APIs for Game Assets - Complete Guide

## 🚀 **Quick Start with Stability AI (Recommended)**

### 1. **Get API Key:**
```bash
# Visit: https://platform.stability.ai/
# Sign up and grab your API key
```

### 2. **Update Your .env:**
```bash
# Use Stability AI (best choice for game assets)
IMAGE_PROVIDER=stability_ai
STABILITY_AI_API_KEY=sk-your-actual-key-here

# AWS S3 Configuration
AWS_ACCESS_KEY_ID=your_aws_key
AWS_SECRET_ACCESS_KEY=your_aws_secret  
S3_BUCKET_NAME=mobiarty-assets

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
```

### 3. **Run Your App:**
```bash
# Start Redis
docker run -d -p 6379:6379 redis:7-alpine

# Start the Python worker
python main.py
```

### 4. **Test Generation:**
```bash
python test_workflow.py
```

## 🎯 **Style Prompts for Game Assets**

### **Pixel Art Style:**
```
"A fierce dragon, pixel art style, 16-bit game sprite, clean background, game asset"
```

### **2D Game Character:**
```  
"A fantasy knight character, 2D game art, clean lines, game sprite, front view"
```

### **Environment Asset:**
```
"A mystical forest background, 2D game art, parallax layer, game environment"
```