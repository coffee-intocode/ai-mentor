# API Usage Examples

Complete examples for testing the new API endpoints.

## Setup

```bash
# Start the server
cd backend/agent
uvicorn chatbot.app:app --reload --port 8080
```

## Base URL
```
http://localhost:8080/api/v1
```

## 🧑 User Endpoints

### Create a User
```bash
curl -X POST "http://localhost:8080/api/v1/users" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "alice@example.com",
    "username": "alice"
  }'

# Response (201 Created)
{
  "id": 1,
  "email": "alice@example.com",
  "username": "alice",
  "created_at": "2024-01-01T10:00:00Z",
  "updated_at": "2024-01-01T10:00:00Z"
}
```

### Get User by ID
```bash
curl "http://localhost:8080/api/v1/users/1"

# Response (200 OK)
{
  "id": 1,
  "email": "alice@example.com",
  "username": "alice",
  "created_at": "2024-01-01T10:00:00Z",
  "updated_at": "2024-01-01T10:00:00Z"
}
```

### Get User by Email
```bash
curl "http://localhost:8080/api/v1/users/email/alice@example.com"

# Response (200 OK)
{
  "id": 1,
  "email": "alice@example.com",
  "username": "alice",
  "created_at": "2024-01-01T10:00:00Z",
  "updated_at": "2024-01-01T10:00:00Z"
}
```

### Update User
```bash
curl -X PATCH "http://localhost:8080/api/v1/users/1" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "alice_updated"
  }'

# Response (200 OK)
{
  "id": 1,
  "email": "alice@example.com",
  "username": "alice_updated",
  "created_at": "2024-01-01T10:00:00Z",
  "updated_at": "2024-01-01T10:05:00Z"
}
```

### Delete User
```bash
curl -X DELETE "http://localhost:8080/api/v1/users/1"

# Response (204 No Content)
```

## 💬 Conversation Endpoints

### Create a Conversation
```bash
curl -X POST "http://localhost:8080/api/v1/conversations" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "title": "My First Conversation"
  }'

# Response (201 Created)
{
  "id": 1,
  "user_id": 1,
  "title": "My First Conversation",
  "created_at": "2024-01-01T10:00:00Z",
  "updated_at": "2024-01-01T10:00:00Z"
}
```

### Get Conversation by ID
```bash
curl "http://localhost:8080/api/v1/conversations/1"

# Response (200 OK)
{
  "id": 1,
  "user_id": 1,
  "title": "My First Conversation",
  "created_at": "2024-01-01T10:00:00Z",
  "updated_at": "2024-01-01T10:00:00Z"
}
```

### Get User's Conversations
```bash
curl "http://localhost:8080/api/v1/conversations/user/1"

# Response (200 OK)
[
  {
    "id": 1,
    "user_id": 1,
    "title": "My First Conversation",
    "created_at": "2024-01-01T10:00:00Z",
    "updated_at": "2024-01-01T10:00:00Z"
  },
  {
    "id": 2,
    "user_id": 1,
    "title": "Another Conversation",
    "created_at": "2024-01-01T11:00:00Z",
    "updated_at": "2024-01-01T11:00:00Z"
  }
]
```

### Update Conversation
```bash
curl -X PATCH "http://localhost:8080/api/v1/conversations/1" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Updated Title"
  }'

# Response (200 OK)
{
  "id": 1,
  "user_id": 1,
  "title": "Updated Title",
  "created_at": "2024-01-01T10:00:00Z",
  "updated_at": "2024-01-01T10:10:00Z"
}
```

### Delete Conversation
```bash
curl -X DELETE "http://localhost:8080/api/v1/conversations/1"

# Response (204 No Content)
```

## 📨 Message Endpoints

### Create a Message
```bash
curl -X POST "http://localhost:8080/api/v1/messages" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": 1,
    "role": "user",
    "content": "Hello, AI! How are you?"
  }'

# Response (201 Created)
{
  "id": 1,
  "conversation_id": 1,
  "role": "user",
  "content": "Hello, AI! How are you?",
  "created_at": "2024-01-01T10:00:00Z"
}
```

### Get Message by ID
```bash
curl "http://localhost:8080/api/v1/messages/1"

# Response (200 OK)
{
  "id": 1,
  "conversation_id": 1,
  "role": "user",
  "content": "Hello, AI! How are you?",
  "created_at": "2024-01-01T10:00:00Z"
}
```

### Get Conversation Messages
```bash
curl "http://localhost:8080/api/v1/messages/conversation/1"

# Response (200 OK)
[
  {
    "id": 1,
    "conversation_id": 1,
    "role": "user",
    "content": "Hello, AI! How are you?",
    "created_at": "2024-01-01T10:00:00Z"
  },
  {
    "id": 2,
    "conversation_id": 1,
    "role": "assistant",
    "content": "I'm doing great! How can I help you?",
    "created_at": "2024-01-01T10:00:01Z"
  }
]
```

## 💡 Chat Endpoint (Integrated)

### Send a Chat Message (New Conversation)
```bash
curl -X POST "http://localhost:8080/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "message": "What is FastAPI?",
    "conversation_id": null
  }'

# Response (200 OK)
{
  "conversation_id": 3,
  "user_message": {
    "id": 5,
    "content": "What is FastAPI?"
  },
  "assistant_message": {
    "id": 6,
    "content": "Echo: What is FastAPI?"
  }
}
```

### Send a Chat Message (Existing Conversation)
```bash
curl -X POST "http://localhost:8080/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "message": "Tell me more!",
    "conversation_id": 3
  }'

# Response (200 OK)
{
  "conversation_id": 3,
  "user_message": {
    "id": 7,
    "content": "Tell me more!"
  },
  "assistant_message": {
    "id": 8,
    "content": "Echo: Tell me more!"
  }
}
```

## 🏥 Health Check

```bash
curl "http://localhost:8080/health"

# Response (200 OK)
{
  "status": "healthy",
  "app_name": "AI Mentor API",
  "version": "0.1.0",
  "environment": "development"
}
```

## 🔄 Complete Workflow Example

### 1. Create a User
```bash
USER_RESPONSE=$(curl -s -X POST "http://localhost:8080/api/v1/users" \
  -H "Content-Type: application/json" \
  -d '{"email": "bob@example.com", "username": "bob"}')

USER_ID=$(echo $USER_RESPONSE | jq -r '.id')
echo "Created user with ID: $USER_ID"
```

### 2. Start a Chat (Creates Conversation)
```bash
CHAT_RESPONSE=$(curl -s -X POST "http://localhost:8080/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d "{\"user_id\": $USER_ID, \"message\": \"Hello AI!\", \"conversation_id\": null}")

CONV_ID=$(echo $CHAT_RESPONSE | jq -r '.conversation_id')
echo "Created conversation with ID: $CONV_ID"
```

### 3. Continue the Conversation
```bash
curl -X POST "http://localhost:8080/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d "{
    \"user_id\": $USER_ID,
    \"message\": \"How does FastAPI work?\",
    \"conversation_id\": $CONV_ID
  }"
```

### 4. Get Conversation History
```bash
curl "http://localhost:8080/api/v1/messages/conversation/$CONV_ID"
```

### 5. Get All User Conversations
```bash
curl "http://localhost:8080/api/v1/conversations/user/$USER_ID"
```

## 🐍 Python Examples

### Using `requests` Library

```python
import requests

BASE_URL = "http://localhost:8080/api/v1"

# Create a user
response = requests.post(
    f"{BASE_URL}/users",
    json={"email": "charlie@example.com", "username": "charlie"}
)
user = response.json()
print(f"Created user: {user['id']}")

# Start a chat
response = requests.post(
    f"{BASE_URL}/chat",
    json={
        "user_id": user["id"],
        "message": "Hello!",
        "conversation_id": None
    }
)
chat = response.json()
print(f"Conversation ID: {chat['conversation_id']}")
print(f"AI Response: {chat['assistant_message']['content']}")

# Continue conversation
response = requests.post(
    f"{BASE_URL}/chat",
    json={
        "user_id": user["id"],
        "message": "Tell me more!",
        "conversation_id": chat["conversation_id"]
    }
)
chat = response.json()
print(f"AI Response: {chat['assistant_message']['content']}")
```

### Using `httpx` (Async)

```python
import asyncio
import httpx

BASE_URL = "http://localhost:8080/api/v1"

async def main():
    async with httpx.AsyncClient() as client:
        # Create user
        response = await client.post(
            f"{BASE_URL}/users",
            json={"email": "diana@example.com", "username": "diana"}
        )
        user = response.json()
        
        # Start chat
        response = await client.post(
            f"{BASE_URL}/chat",
            json={
                "user_id": user["id"],
                "message": "Hi AI!",
                "conversation_id": None
            }
        )
        chat = response.json()
        print(f"AI: {chat['assistant_message']['content']}")

asyncio.run(main())
```

## 🧪 Testing with pytest

```python
from fastapi.testclient import TestClient
from chatbot.app import app

client = TestClient(app)

def test_create_user():
    response = client.post(
        "/api/v1/users",
        json={"email": "test@example.com", "username": "test"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"
    assert "id" in data

def test_chat_flow():
    # Create user
    user_response = client.post(
        "/api/v1/users",
        json={"email": "chat@example.com", "username": "chatuser"}
    )
    user_id = user_response.json()["id"]
    
    # Send chat message
    chat_response = client.post(
        "/api/v1/chat",
        json={
            "user_id": user_id,
            "message": "Test message",
            "conversation_id": None
        }
    )
    assert chat_response.status_code == 200
    data = chat_response.json()
    assert "conversation_id" in data
    assert "assistant_message" in data
```

## 📱 Frontend Integration Examples

### React/TypeScript

```typescript
const API_BASE = 'http://localhost:8080/api/v1';

interface ChatRequest {
  user_id: number;
  message: string;
  conversation_id?: number | null;
}

interface ChatResponse {
  conversation_id: number;
  user_message: { id: number; content: string };
  assistant_message: { id: number; content: string };
}

async function sendChatMessage(data: ChatRequest): Promise<ChatResponse> {
  const response = await fetch(`${API_BASE}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  
  if (!response.ok) {
    throw new Error('Chat request failed');
  }
  
  return response.json();
}

// Usage
const chat = await sendChatMessage({
  user_id: 1,
  message: 'Hello!',
  conversation_id: null,
});

console.log(chat.assistant_message.content);
```

### Vue.js

```javascript
const apiClient = {
  baseURL: 'http://localhost:8080/api/v1',
  
  async createUser(email, username) {
    const response = await fetch(`${this.baseURL}/users`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, username }),
    });
    return response.json();
  },
  
  async sendChat(userId, message, conversationId = null) {
    const response = await fetch(`${this.baseURL}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_id: userId,
        message,
        conversation_id: conversationId,
      }),
    });
    return response.json();
  },
};

// Usage in component
export default {
  methods: {
    async handleChat() {
      const result = await apiClient.sendChat(
        this.userId,
        this.message,
        this.conversationId
      );
      this.messages.push(result.assistant_message);
    },
  },
};
```

## 🔍 Error Responses

### 400 Bad Request
```json
{
  "detail": "User with this email already exists"
}
```

### 404 Not Found
```json
{
  "detail": "User not found"
}
```

### 422 Validation Error
```json
{
  "detail": [
    {
      "type": "string_type",
      "loc": ["body", "email"],
      "msg": "Input should be a valid string",
      "input": 123
    }
  ]
}
```

## 📊 OpenAPI/Swagger UI

Access interactive documentation at:
- **Swagger UI**: http://localhost:8080/api/v1/docs
- **ReDoc**: http://localhost:8080/api/v1/redoc

Try all endpoints directly from the browser!

---

**Happy API Testing!** 🚀

