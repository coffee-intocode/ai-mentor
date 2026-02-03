# Backend Agent Notes

## Purpose
- FastAPI backend for AI Mentor with chat APIs, Supabase auth, and RAG ingestion/retrieval.
- Uses a layered architecture: routers -> services -> repositories -> models.

## Quick start
- Install deps: `uv sync`
- Configure env: `cp env.example .env` (set `SUPABASE_DATABASE_URL`, `SUPABASE_URL`, API keys)
- Run API: `uv run uvicorn chatbot.app:app --reload --port 8080` or `make dev`
- Migrations: `make migrate` (Alembic in `alembic/`)

## Entry points
- `chatbot/app.py`: FastAPI app factory, CORS, security headers, router wiring, `/health`.
- `chatbot/agent.py`: Pydantic AI agent and `retrieve` tool for RAG.
- `chatbot/database.py`: async engine/session, `get_db_session`, `init_db`.
- `chatbot/models.py`: SQLAlchemy models (users, conversations, messages, documents, document_sections).

## API surface
- `/api/configure` (GET): available AI models and built-in tools (auth required).
- `/api/chat` (POST): streaming AI chat via `VercelAIAdapter` (auth required).
- `/api/v1/users`, `/api/v1/conversations`, `/api/v1/messages`: CRUD endpoints (auth required).
- `/api/v1/documents`: upload/list documents for RAG (auth required).
- `/api/v1/chat`: legacy chat endpoint (currently stubbed with echo response).
- `/health`: health check with optional DB connectivity check.

## Auth flow
- `chatbot/auth/dependencies.py` validates Supabase JWT via JWKS and returns `CurrentUser`.
- `get_current_user` auto-creates a local `User` row based on Supabase `sub` and `email`.
- Requires `SUPABASE_URL` in env; APIs using `CurrentUser` expect `Authorization: Bearer <token>`.

## RAG pipeline
- Upload in `chatbot/routers/documents.py` -> `IngestionService`.
- `ReductoService` parses and returns text plus `job_id` for pipelining.
- `IngestionService` chunks text with overlap, creates Voyage embeddings, stores `document_sections`.
- `RetrievalService` runs pgvector similarity search (`<#>` distance) for top-k sections.
- `agent.py` exposes a `retrieve` tool that opens a fresh DB session to avoid streaming session closure issues.

## AI chat details
- `chatbot/routers/ai_chat.py` defines model/tool catalogs and forwards requests to the agent.
- Models: `anthropic:claude-sonnet-4-5`, `openai-responses:gpt-5`, `google-gla:gemini-2.5-pro`.
- Tools: `web_search`, `code_execution`, `image_generation`.
- `haystack_ai` is initialized in `app.py` for tracing/instrumentation.

## Configuration
- `chatbot/config.py` reads `.env` using `pydantic-settings` (CORS, DB URLs, API keys).
- Embeddings require `VOYAGE_API_KEY`; parsing requires `REDUCTO_API_KEY`.
- DB requires `SUPABASE_DATABASE_URL` (asyncpg connection string).

## Deployment and ops
- `makefile` provides local dev, migrations, and Docker/ECS deployment helpers.
- `docker-compose.yml` starts local services; `terraform/` and `deploy.sh` handle infra.

## Notes and gotchas
- The frontend uses `/api/chat` (streaming), not `/api/v1/chat` (legacy echo).
- If `SUPABASE_DATABASE_URL` is missing, DB dependencies raise at runtime.
- `haystack_ai.init` is currently configured with a local endpoint and a hardcoded key in `chatbot/app.py`.
