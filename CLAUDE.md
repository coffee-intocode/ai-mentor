# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI Mentor is a full-stack AI chat application with a React frontend and Python FastAPI backend. It features conversation management, RAG (Retrieval-Augmented Generation) capabilities, and integrates with multiple AI providers (Anthropic, Google, OpenAI) via Pydantic AI.

## Development Commands

### Frontend (from `frontend/`)
```bash
npm install
npm run dev              # Start dev server on :5173 (proxies /api to :8080)
npm run build            # Production build
npm run typecheck        # Type check without emitting
npm run lint             # Run ESLint
npm run lint-fix         # Fix ESLint issues
npm run format           # Format with Prettier
```

### Backend (from `backend/agent/`)
```bash
uv sync                  # Install dependencies
make dev                 # Start server on :8080 with hot reload
make migrate             # Run database migrations
make migrate-create      # Create new migration (interactive prompt)
make migrate-status      # Check current migration status
```

### Docker & Deployment
```bash
make up                  # Docker Compose up (local dev with PostgreSQL)
make down                # Docker Compose down
make build-image         # Build Docker image
make build-image-push    # Build and push to AWS ECR
make deploy              # Deploy to ECS
```

## Architecture

### Frontend (`frontend/`)

**Stack**: React 19, TypeScript, Vite, Tailwind CSS 4, Vercel AI SDK

**Key Files**:
- `src/Chat.tsx` - Main chat component with conversation state and localStorage persistence
- `src/Part.tsx` - Renders individual message parts (text, reasoning, tools, sources)
- `src/App.tsx` - Root component with theme provider, sidebar, React Query setup
- `src/components/ai-elements/` - Vercel AI Elements wrappers for chat UI

**Patterns**:
- Conversations stored in localStorage by nanoid ID
- URL routing: `/` for new chat, `/{nanoid}` for existing conversations
- Messages synced to localStorage with 500ms throttle
- Dynamic model/tool configuration fetched from `/api/configure`

### Backend (`backend/agent/chatbot/`)

**Stack**: FastAPI, Python 3.12+, SQLAlchemy 2.0 (async), Pydantic AI, Supabase (PostgreSQL + pgvector)

**Layered Architecture**:
```
Routers (API endpoints) → Services (business logic) → Repositories (data access) → Models (ORM)
```

**Key Directories**:
- `routers/` - API endpoints (`ai_chat.py` for AI chat, others for CRUD operations)
- `services/` - Business logic layer
- `repositories/` - Database operations with base repository pattern
- `schemas/` - Pydantic request/response models
- `models.py` - SQLAlchemy ORM models (User, Conversation, Message, Document, DocumentSection)

**Entry Point**: `chatbot/app.py` - FastAPI application factory

### API Endpoints

- `POST /api/chat` - AI chat with streaming (SSE)
- `GET /api/configure` - Available models and builtin tools
- `/api/v1/users/*`, `/api/v1/conversations/*`, `/api/v1/messages/*` - CRUD operations
- `/api/v1/documents/*` - Document management for RAG
- `GET /health` - Health check
- `GET /api/v1/docs` - Swagger UI

## Configuration

### Frontend
- TypeScript paths: `@/*` maps to `./src/*`
- Dev proxy: `/api` → `localhost:8080`

### Backend
Environment variables (see `env.example`):
- `SUPABASE_DATABASE_URL` - PostgreSQL connection string (required)
- `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GOOGLE_API_KEY` - AI provider keys
- `REDUCTO_API_KEY`, `VOYAGE_API_KEY` - Document processing and embeddings

### Package Management
- Frontend: npm with `package-lock.json`
- Backend: uv with `pyproject.toml` and `uv.lock`
