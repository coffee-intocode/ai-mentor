# Testing RAG Feature Through Frontend

This guide explains how to test the RAG (Retrieval-Augmented Generation) feature through the frontend using `selfindulgence.pdf`.

## Prerequisites

1. Database setup with pgvector extension
2. Environment variables configured:
   - `SUPABASE_DATABASE_URL`
   - `VOYAGE_API_KEY` (for embeddings)
   - `REDUCTO_API_KEY` (for document parsing)
   - `ANTHROPIC_API_KEY` (for Claude)

## Step 1: Ingest the Test Document

First, ingest the test PDF into the database:

```bash
cd backend/agent
python scripts/ingest_test_document.py
```

This will:

- Parse `pg_essays/selfindulgence.pdf` using Reducto
- Chunk the content into 512-word sections with 15% overlap
- Generate embeddings using Voyage AI
- Store everything in the database

## Step 2: Start the Backend

```bash
cd backend/agent
uvicorn chatbot.app:app --reload --port 8080
```

The API will be available at `http://localhost:8080`

## Step 3: Start the Frontend

```bash
cd frontend
npm run dev
```

The frontend will be available at `http://localhost:5173` (or similar)

## Step 4: Test RAG Through Chat

Open the frontend and ask questions about the essay:

### Test Questions:

1. **"What is the main point of this essay?"**

   - Should summarize the essay about how people lose time and money

2. **"How do people lose money according to the author?"**

   - Should mention: through bad investments, not excessive spending

3. **"What is fake work?"**

   - Should explain: work that seems productive but accomplishes nothing (like email)

4. **"What are the alarms the author talks about?"**

   - Should mention: natural alarms about self-indulgence vs learned alarms about investments

5. **"What's the difference between losing time and losing money?"**
   - Should compare: both have similar patterns, bypassing natural warning systems

## Expected Behavior

When you ask these questions:

1. The frontend sends your message to `/api/chat`
2. The backend agent uses the `retrieve` tool to search the document
3. The agent finds relevant sections from the essay
4. The agent synthesizes an answer citing the source
5. The response streams back to the frontend

## Debugging

### Check if document is ingested:

```bash
cd backend/agent
python -c "
import asyncio
from chatbot.database import AsyncSessionLocal
from chatbot.models import Document
from sqlalchemy import select

async def check():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Document))
        docs = result.scalars().all()
        for doc in docs:
            print(f'Document: {doc.filename}, Status: {doc.status}')

asyncio.run(check())
"
```

### Test retrieval directly:

```bash
cd backend/agent
python -c "
import asyncio
from chatbot.database import AsyncSessionLocal
from chatbot.services.retrieval import RetrievalService

async def test():
    async with AsyncSessionLocal() as db:
        service = RetrievalService(db)
        results = await service.retrieve('How do people lose money?')
        print(results[:500])

asyncio.run(test())
"
```

### Check backend logs:

Look for:

- `retrieve` tool calls in the logs
- Database queries for vector search
- Retrieved document sections

## Frontend Details

The frontend already has everything needed:

- ✅ Chat interface with streaming
- ✅ Model selection
- ✅ Tool visualization
- ✅ Source citations support

The agent's `retrieve` tool will automatically be available and called when relevant to user questions.

## Success Criteria

✅ Frontend connects to backend
✅ Questions trigger the `retrieve` tool
✅ Agent returns answers based on the essay
✅ Responses cite "selfindulgence.pdf" as source
✅ Answers are accurate to the essay content
