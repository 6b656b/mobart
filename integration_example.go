// integration_example.go
// This shows how to integrate the Python Mobart app with your Go backend

package main

import (
	"context"
	"encoding/json"
	"log"
	"time"

	"github.com/go-redis/redis/v8"
	"github.com/google/uuid"
)

// Redis client setup
var rdb *redis.Client

func init() {
	rdb = redis.NewClient(&redis.Options{
		Addr:     "localhost:6379",
		Password: "", // no password
		DB:       0,  // default DB
	})
}

// Request structure to send to Python app
type ImageGenerationRequest struct {
	RequestID string `json:"request_id"`
	UserID    string `json:"user_id"`
	Prompt    string `json:"prompt"`
}

// Completion structure received from Python app
type ImageGenerationCompletion struct {
	RequestID           string  `json:"request_id"`
	UserID             string  `json:"user_id"`
	Status             string  `json:"status"` // "completed" or "failed"
	S3Key              string  `json:"s3_key,omitempty"`
	S3URL              string  `json:"s3_url,omitempty"`
	GenerationTimeSeconds float64 `json:"generation_time_seconds,omitempty"`
	Error              string  `json:"error,omitempty"`
	Timestamp          string  `json:"timestamp"`
}

// PublishImageGenerationRequest sends a request to the Python app
func PublishImageGenerationRequest(userID, prompt string) (string, error) {
	requestID := uuid.New().String()
	
	request := ImageGenerationRequest{
		RequestID: requestID,
		UserID:    userID,
		Prompt:    prompt,
	}

	jsonData, err := json.Marshal(request)
	if err != nil {
		return "", err
	}

	err = rdb.Publish(context.Background(), "image_generation_requests", jsonData).Err()
	if err != nil {
		return "", err
	}

	log.Printf("📤 Published generation request: %s", requestID)
	return requestID, nil
}

// StartCompletionListener listens for completion notifications from Python app
func StartCompletionListener() {
	pubsub := rdb.Subscribe(context.Background(), "image_generation_complete")
	defer pubsub.Close()

	log.Println("👂 Listening for image generation completions...")

	for msg := range pubsub.Channel() {
		var completion ImageGenerationCompletion
		if err := json.Unmarshal([]byte(msg.Payload), &completion); err != nil {
			log.Printf("❌ Failed to parse completion: %v", err)
			continue
		}

		log.Printf("📥 Received completion for request %s: %s", completion.RequestID, completion.Status)

		if completion.Status == "completed" {
			// Update your database with the S3 URL
			err := UpdateGeneratedContentWithImage(completion.RequestID, completion.S3Key, completion.S3URL)
			if err != nil {
				log.Printf("❌ Failed to update database: %v", err)
			} else {
				log.Printf("✅ Updated database for request %s", completion.RequestID)
			}
		} else if completion.Status == "failed" {
			// Handle failure
			log.Printf("❌ Generation failed for request %s: %s", completion.RequestID, completion.Error)
			// You might want to update the database to mark this request as failed
		}
	}
}

// UpdateGeneratedContentWithImage updates your database with the generated image
func UpdateGeneratedContentWithImage(requestID, s3Key, s3URL string) error {
	// This is where you'd update your generated_content table
	// Example SQL would be:
	// UPDATE generated_content 
	// SET content_url = $1, text_response = $2, content_type = 'image'
	// WHERE request_id = $3

	log.Printf("🔄 Updating database: request_id=%s, s3_key=%s, s3_url=%s", requestID, s3Key, s3URL)
	
	// Your database update logic here
	// For example, using your existing genRepo:
	// return genRepo.UpdateWithImageURL(requestID, s3Key, s3URL)
	
	return nil // placeholder
}

// Modified version of your protected endpoint
func protectedEndpointWithAsyncGeneration(c *gin.Context) {
	var req RequestPayload
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid JSON format"})
		return
	}

	log.Println("Received request:", req.Text, "Type:", req.RequestType)
	user := c.MustGet("currentUser").(*repository.User)
	reqID := uuid.New()

	// Store the request in database
	reqRepo.Create(reqID, user.ID, req.RequestType, req.Text)

	requestType := req.RequestType
	if requestType == "" {
		requestType = "text"
	}

	if requestType == "image" {
		// Instead of generating immediately, publish to Redis
		generationRequestID, err := PublishImageGenerationRequest(user.ID.String(), req.Text)
		if err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to queue image generation"})
			return
		}

		// Store the generation request ID for tracking
		// You might want to update your database to store this relationship

		c.JSON(http.StatusAccepted, gin.H{
			"type": "image",
			"status": "queued",
			"generation_request_id": generationRequestID,
			"message": "Image generation queued. You'll receive a notification when complete."
		})
	} else {
		// Handle text processing as before
		respText := req.Text + "+haha"
		
		// Save to database as before
		if err := genRepo.Create(
			user.ID,
			reqID,
			time.Now(),
			respText,
			"text",
			"",
			false,
		); err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": "cannot save generated content"})
			return
		}

		c.JSON(http.StatusOK, gin.H{
			"type": "text",
			"data": respText,
		})
	}
}

func main() {
	log.Println("🚀 Starting Go backend with Redis integration...")

	// Start the completion listener in a goroutine
	go StartCompletionListener()

	// Example: publish a test request
	time.Sleep(2 * time.Second)
	_, err := PublishImageGenerationRequest("test-user-id", "A fierce dragon with glowing eyes")
	if err != nil {
		log.Printf("Failed to publish test request: %v", err)
	}

	// Keep the program running
	select {}
}
