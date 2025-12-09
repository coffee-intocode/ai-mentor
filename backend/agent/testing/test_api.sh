#!/bin/bash

# API Testing Script for AI Mentor Backend
# This script contains curl commands for testing all API endpoints
# 
# Usage: 
#   chmod +x test_api.sh
#   ./test_api.sh
#
# Or run individual commands by copying them

# Configuration
BASE_URL="http://localhost:8080"
API_PREFIX="/api/v1"
CONTENT_TYPE="Content-Type: application/json"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Helper function to print section headers
print_section() {
    echo -e "\n${BLUE}================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================${NC}\n"
}

# Helper function to print test names
print_test() {
    echo -e "${YELLOW}➜ $1${NC}"
}

print_section "AI MENTOR API TEST SUITE"

# ================================
# USERS ROUTER TESTS
# ================================
print_section "USERS ROUTER (/users)"

# Create User
print_test "1. Create a new user"
curl -X POST "$BASE_URL$API_PREFIX/users" \
  -H "$CONTENT_TYPE" \
  -d '{
    "email": "test@example.com",
    "username": "testuser"
  }'
echo -e "\n"

print_test "2. Create another user"
curl -X POST "$BASE_URL$API_PREFIX/users" \
  -H "$CONTENT_TYPE" \
  -d '{
    "email": "alice@example.com",
    "username": "alice"
  }'
echo -e "\n"

print_test "3. Create user without username (optional)"
curl -X POST "$BASE_URL$API_PREFIX/users" \
  -H "$CONTENT_TYPE" \
  -d '{
    "email": "bob@example.com"
  }'
echo -e "\n"

# Get User by ID
print_test "4. Get user by ID (user_id: 1)"
curl -X GET "$BASE_URL$API_PREFIX/users/1"
echo -e "\n"

print_test "5. Get user by ID (user_id: 2)"
curl -X GET "$BASE_URL$API_PREFIX/users/2"
echo -e "\n"

# Get User by Email
print_test "6. Get user by email"
curl -X GET "$BASE_URL$API_PREFIX/users/email/test@example.com"
echo -e "\n"

print_test "7. Get user by email (alice)"
curl -X GET "$BASE_URL$API_PREFIX/users/email/alice@example.com"
echo -e "\n"

# Update User
print_test "8. Update user username"
curl -X PATCH "$BASE_URL$API_PREFIX/users/1" \
  -H "$CONTENT_TYPE" \
  -d '{
    "username": "updated_testuser"
  }'
echo -e "\n"

# Delete User (commented out by default to preserve test data)
# print_test "9. Delete user"
# curl -X DELETE "$BASE_URL$API_PREFIX/users/3"
# echo -e "\n"

# ================================
# CONVERSATIONS ROUTER TESTS
# ================================
print_section "CONVERSATIONS ROUTER (/conversations)"

# Create Conversation
print_test "1. Create a conversation for user 1"
curl -X POST "$BASE_URL$API_PREFIX/conversations" \
  -H "$CONTENT_TYPE" \
  -d '{
    "user_id": 1,
    "title": "My First Chat"
  }'
echo -e "\n"

print_test "2. Create conversation without title (optional)"
curl -X POST "$BASE_URL$API_PREFIX/conversations" \
  -H "$CONTENT_TYPE" \
  -d '{
    "user_id": 1
  }'
echo -e "\n"

print_test "3. Create conversation for user 2"
curl -X POST "$BASE_URL$API_PREFIX/conversations" \
  -H "$CONTENT_TYPE" \
  -d '{
    "user_id": 2,
    "title": "Alice'\''s Conversation"
  }'
echo -e "\n"

# Get Conversation by ID
print_test "4. Get conversation by ID (conversation_id: 1)"
curl -X GET "$BASE_URL$API_PREFIX/conversations/1"
echo -e "\n"

print_test "5. Get conversation by ID (conversation_id: 2)"
curl -X GET "$BASE_URL$API_PREFIX/conversations/2"
echo -e "\n"

# Get User Conversations
print_test "6. Get all conversations for user 1"
curl -X GET "$BASE_URL$API_PREFIX/conversations/user/1"
echo -e "\n"

print_test "7. Get all conversations for user 2"
curl -X GET "$BASE_URL$API_PREFIX/conversations/user/2"
echo -e "\n"

# Update Conversation
print_test "8. Update conversation title"
curl -X PATCH "$BASE_URL$API_PREFIX/conversations/1" \
  -H "$CONTENT_TYPE" \
  -d '{
    "title": "Updated Chat Title"
  }'
echo -e "\n"

# Delete Conversation (commented out by default to preserve test data)
# print_test "9. Delete conversation"
# curl -X DELETE "$BASE_URL$API_PREFIX/conversations/2"
# echo -e "\n"

# ================================
# MESSAGES ROUTER TESTS
# ================================
print_section "MESSAGES ROUTER (/messages)"

# Create Messages
print_test "1. Create user message in conversation 1"
curl -X POST "$BASE_URL$API_PREFIX/messages" \
  -H "$CONTENT_TYPE" \
  -d '{
    "conversation_id": 1,
    "role": "user",
    "content": "Hello, how are you?"
  }'
echo -e "\n"

print_test "2. Create assistant message in conversation 1"
curl -X POST "$BASE_URL$API_PREFIX/messages" \
  -H "$CONTENT_TYPE" \
  -d '{
    "conversation_id": 1,
    "role": "assistant",
    "content": "I'\''m doing well, thank you! How can I help you today?"
  }'
echo -e "\n"

print_test "3. Create system message"
curl -X POST "$BASE_URL$API_PREFIX/messages" \
  -H "$CONTENT_TYPE" \
  -d '{
    "conversation_id": 1,
    "role": "system",
    "content": "You are a helpful AI assistant."
  }'
echo -e "\n"

print_test "4. Create another user message"
curl -X POST "$BASE_URL$API_PREFIX/messages" \
  -H "$CONTENT_TYPE" \
  -d '{
    "conversation_id": 1,
    "role": "user",
    "content": "Can you explain Python decorators?"
  }'
echo -e "\n"

# Get Message by ID
print_test "5. Get message by ID (message_id: 1)"
curl -X GET "$BASE_URL$API_PREFIX/messages/1"
echo -e "\n"

print_test "6. Get message by ID (message_id: 2)"
curl -X GET "$BASE_URL$API_PREFIX/messages/2"
echo -e "\n"

# Get Conversation Messages
print_test "7. Get all messages in conversation 1"
curl -X GET "$BASE_URL$API_PREFIX/messages/conversation/1"
echo -e "\n"

print_test "8. Get all messages in conversation 3"
curl -X GET "$BASE_URL$API_PREFIX/messages/conversation/3"
echo -e "\n"

# ================================
# CHAT ROUTER TESTS
# ================================
print_section "CHAT ROUTER (/chat)"

# Chat without existing conversation (creates new one)
print_test "1. Send chat message (creates new conversation)"
curl -X POST "$BASE_URL$API_PREFIX/chat" \
  -H "$CONTENT_TYPE" \
  -d '{
    "user_id": 1,
    "message": "What is machine learning?"
  }'
echo -e "\n"

# Chat with existing conversation
print_test "2. Send chat message to existing conversation"
curl -X POST "$BASE_URL$API_PREFIX/chat" \
  -H "$CONTENT_TYPE" \
  -d '{
    "user_id": 1,
    "conversation_id": 1,
    "message": "Tell me more about neural networks."
  }'
echo -e "\n"

print_test "3. Another chat message in new conversation"
curl -X POST "$BASE_URL$API_PREFIX/chat" \
  -H "$CONTENT_TYPE" \
  -d '{
    "user_id": 2,
    "message": "Explain quantum computing in simple terms."
  }'
echo -e "\n"

# ================================
# AI CHAT ROUTER TESTS
# ================================
print_section "AI CHAT ROUTER (Pydantic AI)"

# Get Configuration
print_test "1. Get AI configuration (models and tools)"
curl -X GET "$BASE_URL$API_PREFIX/configure"
echo -e "\n"

# OPTIONS for CORS
print_test "2. CORS preflight for chat"
curl -X OPTIONS "$BASE_URL$API_PREFIX/chat" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Content-Type"
echo -e "\n"

# AI Chat with streaming (Note: this uses Vercel AI SDK format)
print_test "3. AI chat with Claude Sonnet 4.5 (streaming)"
curl -X POST "$BASE_URL$API_PREFIX/chat" \
  -H "$CONTENT_TYPE" \
  -d '{
    "messages": [
      {
        "role": "user",
        "content": "Hello, can you help me with Python?"
      }
    ],
    "model": "anthropic:claude-sonnet-4-5",
    "builtinTools": []
  }'
echo -e "\n"

print_test "4. AI chat with web search tool"
curl -X POST "$BASE_URL$API_PREFIX/chat" \
  -H "$CONTENT_TYPE" \
  -d '{
    "messages": [
      {
        "role": "user",
        "content": "What is the latest news about AI?"
      }
    ],
    "model": "anthropic:claude-sonnet-4-5",
    "builtinTools": ["web_search"]
  }'
echo -e "\n"

print_test "5. AI chat with code execution tool"
curl -X POST "$BASE_URL$API_PREFIX/chat" \
  -H "$CONTENT_TYPE" \
  -d '{
    "messages": [
      {
        "role": "user",
        "content": "Write a Python function to calculate fibonacci numbers"
      }
    ],
    "model": "openai-responses:gpt-5",
    "builtinTools": ["code_execution"]
  }'
echo -e "\n"

print_test "6. AI chat with multiple tools"
curl -X POST "$BASE_URL$API_PREFIX/chat" \
  -H "$CONTENT_TYPE" \
  -d '{
    "messages": [
      {
        "role": "user",
        "content": "Search for Python best practices and show me code examples"
      }
    ],
    "model": "openai-responses:gpt-5",
    "builtinTools": ["web_search", "code_execution"]
  }'
echo -e "\n"

# ================================
# ERROR CASES TESTS
# ================================
print_section "ERROR CASES"

print_test "1. Get non-existent user (should return 404)"
curl -X GET "$BASE_URL$API_PREFIX/users/9999"
echo -e "\n"

print_test "2. Get non-existent conversation (should return 404)"
curl -X GET "$BASE_URL$API_PREFIX/conversations/9999"
echo -e "\n"

print_test "3. Create user with invalid email (should return 422)"
curl -X POST "$BASE_URL$API_PREFIX/users" \
  -H "$CONTENT_TYPE" \
  -d '{
    "email": "not-an-email",
    "username": "testuser"
  }'
echo -e "\n"

print_test "4. Create message with invalid role (should return 422)"
curl -X POST "$BASE_URL$API_PREFIX/messages" \
  -H "$CONTENT_TYPE" \
  -d '{
    "conversation_id": 1,
    "role": "invalid_role",
    "content": "This should fail"
  }'
echo -e "\n"

print_test "5. Create conversation for non-existent user (should fail)"
curl -X POST "$BASE_URL$API_PREFIX/conversations" \
  -H "$CONTENT_TYPE" \
  -d '{
    "user_id": 9999,
    "title": "This should fail"
  }'
echo -e "\n"

print_section "TEST SUITE COMPLETE"
echo -e "${GREEN}All tests executed!${NC}"
echo -e "${GREEN}Check the responses above for any errors.${NC}\n"

