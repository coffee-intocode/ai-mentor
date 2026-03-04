# AI Mentor

A full-stack AI chat application with a production-grade RAG pipeline — ask questions and get answers grounded in real documents, with citations.

**Live demo:** [aimentor.up.railway.app](https://aimentor.up.railway.app/)

The demo is loaded with Paul Graham's essays. Ask about your favorite essay or try asking:

- _"What are the fundamentals for doing things that don't scale?"_
- _"How can I avoid being default dead in my startup?"_
- _"How should I think about fundraising for my startup?"_
- _"How do I find an idea to work on?"_
- _"How would you advise me to do great work?"_
- _"If I want to build a startup someday, how should I think about where I live?"_

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Browser                                 │
│  React 19 · TypeScript · Tailwind · Vercel AI SDK · shadcn/ui   │
└──────────────────────────────┬──────────────────────────────────┘
                               │ SSE (streaming)
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FastAPI (Python 3.12)                      │
│                                                                 │
│  Routers  →  Services  →  Repositories  →  SQLAlchemy Models   │
│                                                                 │
│     Pydantic AI Agent  ──►  retrieve() tool                     │
│              │                     │                            │
│              ▼                     ▼                            │
│     Anthropic / OpenAI      Embedding Service                   │
│     / Google (LLM)          (Voyage AI)                         │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                PostgreSQL + pgvector (Supabase)                 │
│         documents · document_sections · conversations           │
│                      messages · users                           │
└─────────────────────────────────────────────────────────────────┘
```

---

## RAG Pipeline

The core technical feature is a two-phase Retrieval-Augmented Generation pipeline.

### Ingestion (offline)

```
PDF File
  → Reducto API          (layout-aware parsing: text, tables, images)
  → Custom chunker       (512-word chunks, ~77-word overlap, pure Python)
  → Voyage AI            (voyage-3.5-lite → 1024-dim vectors, document mode)
  → pgvector             (stored in document_sections table)
```

### Retrieval (runtime)

```
User message
  → Voyage AI            (same model, query mode — different embedding space)
  → pgvector <#>         (inner-product similarity search, top 8 chunks)
  → Pydantic AI tool     (agent decides when to invoke retrieve())
  → LLM                  (generates response with citations)
  → SSE stream           (streamed back to browser)
```

The agent is **agentic RAG**: the LLM decides when retrieval is needed as a tool call rather than retrieving on every request.

---

## Tech Stack

| Layer          | Technologies                                                                           |
| -------------- | -------------------------------------------------------------------------------------- |
| **Frontend**   | React 19, TypeScript, Vite, Tailwind CSS 4, Vercel AI SDK, TanStack Query, shadcn/ui   |
| **Backend**    | Python 3.12, FastAPI (async), Pydantic AI, SQLAlchemy 2.0 (async), Alembic, asyncpg    |
| **AI / ML**    | Anthropic Claude, OpenAI, Google Gemini, Voyage AI (embeddings), Reducto (doc parsing) |
| **Database**   | PostgreSQL + pgvector via Supabase                                                     |
| **Auth**       | Supabase Auth + JWT                                                                    |
| **Streaming**  | Server-Sent Events (SSE Starlette)                                                     |
| **Deployment** | Docker, AWS ECS + ECR, AWS Amplify, Railway, Terraform                                 |

---

## Key Design Decisions

**Agentic RAG over naive RAG** — Rather than always injecting retrieved context, the agent calls `retrieve()` as a tool only when needed. This avoids polluting the context window on conversational turns that don't require document lookup.

**Separate query vs. document embeddings** — Voyage AI distinguishes `input_type="query"` from `input_type="document"`. Using the correct mode for each significantly improves retrieval precision compared to embedding both with the same call.

**Overlap chunking** — Chunks use 15% word overlap (~77 words) to ensure semantic context isn't lost at boundaries, particularly important for essay-style prose where arguments span paragraphs.

**Reducto over basic PDF parsing** — Reducto handles complex document layouts (columns, footnotes, tables) and is pipeline-friendly: the `job_id` from a parse run can be reused for structured extraction without re-uploading.

**Layered backend** — Strict separation of Routers → Services → Repositories keeps business logic testable in isolation and prevents fat route handlers.

---

## Infrastructure & Deployment

The demo runs on Railway for cost-effective portfolio hosting. The production-ready AWS infrastructure is fully defined in Terraform under `backend/agent/terraform/`.

### Demo

| Component   | Hosting                                  |
| ----------- | ---------------------------------------- |
| Backend API | [Railway](https://railway.app/)          |
| Frontend    | [Railway](https://railway.app/)          |
| Database    | Supabase (managed PostgreSQL + pgvector) |

### Production (Terraform / AWS)

```
Frontend  →  AWS Amplify          (Git-connected, CI/CD on push)
Backend   →  AWS ECS (EC2 mode)   (Dockerized, behind ALB)
              ├── Auto Scaling Group (CPU target tracking at 50%)
              ├── Spot instance support (cost savings)
              ├── Rolling deploys with min 50% healthy
              └── CloudWatch Logs (configurable retention)
DNS       →  Route 53 + ACM wildcard certificate
Secrets   →  SSM Parameter Store (injected into containers at runtime)
Network   →  VPC with private subnets + bastion host for DB access
```

The Terraform is modular — `network`, `cluster`, `service`, `acm`, and `dns` are independent reusable modules composed at the environment level, making it straightforward to spin up staging or production environments independently.

---

## Local Development

**Backend** (requires Python 3.12+, `uv`)

```bash
cd backend/agent
cp env.example .env   # add API keys
uv sync
make dev              # starts on :8080
make migrate          # run DB migrations
```

**Frontend** (requires Node 20+)

```bash
cd frontend
npm install
npm run dev           # starts on :5173, proxies /api → :8080
```

**Required environment variables** (see `env.example`):

- `SUPABASE_DATABASE_URL`
- `ANTHROPIC_API_KEY`
- `VOYAGE_API_KEY`
- `REDUCTO_API_KEY`

---

## Project Structure

```
ai-mentor/
├── frontend/
│   └── src/
│       ├── Chat.tsx              # Main chat UI with streaming
│       ├── Part.tsx              # Renders text, reasoning, tool calls, citations
│       ├── App.tsx               # Root with auth, sidebar, React Query
│       └── components/
│           ├── ai-elements/      # Vercel AI SDK wrappers
│           └── ui/               # shadcn/ui components
└── backend/agent/chatbot/
    ├── agent.py                  # Pydantic AI agent + retrieve() tool
    ├── routers/                  # FastAPI endpoints (chat, conversations, documents)
    ├── services/
    │   ├── ingestion.py          # Document ingestion orchestration
    │   ├── embedding.py          # Voyage AI embedding service
    │   ├── retrieval.py          # pgvector similarity search
    │   └── reducto.py            # Reducto document parsing
    ├── repositories/             # Database access layer
    └── models.py                 # SQLAlchemy ORM (User, Conversation, Message, Document, DocumentSection)
```
