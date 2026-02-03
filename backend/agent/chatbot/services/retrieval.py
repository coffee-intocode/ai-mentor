"""Retrieval service for RAG-based document search."""

import json
import logging
from dataclasses import dataclass
from typing import List
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from .embedding import EmbeddingService


@dataclass
class RetrievalResult:
    """A single retrieval result with metadata."""

    chunk_id: str
    document_id: str
    title: str
    content: str
    source: str
    score: float


@dataclass
class RetrievalResponse:
    """Response from the retrieval service with structured results."""

    query: str
    results: List[RetrievalResult]

    def to_formatted_string(self) -> str:
        """Format results as a string for the LLM."""
        if not self.results:
            return "No relevant documents found."

        formatted_results = []
        for result in self.results:
            formatted_results.append(
                f"# {result.title}\n"
                f"Source: {result.source}\n"
                f"Score: {result.score:.4f}\n\n"
                f"{result.content}\n"
            )
        return "\n\n---\n\n".join(formatted_results)

    def to_span_attributes(self) -> dict:
        """Generate span attributes for observability."""
        results_json = [
            {
                "chunk_id": r.chunk_id,
                "document_id": r.document_id,
                "score": r.score,
                "source": r.source,
            }
            for r in self.results
        ]
        return {
            "retrieval.query": self.query,
            "retrieval.results": json.dumps(results_json),
            "retrieval.chunk_ids": json.dumps([r.chunk_id for r in self.results]),
            "retrieval.document_ids": json.dumps(
                list(set(r.document_id for r in self.results))
            ),
        }


class RetrievalService:
    """Service for retrieving relevant document sections."""

    def __init__(self, db: AsyncSession):
        """Initialize the retrieval service.

        Args:
            db: Database session
        """
        self.db = db
        self.embedding_service = EmbeddingService()
        self._logger = logging.getLogger(__name__)

    async def retrieve(self, query: str, top_k: int = 8) -> RetrievalResponse:
        """Retrieve relevant document sections based on a query.

        Args:
            query: The search query
            top_k: Number of results to return

        Returns:
            RetrievalResponse with structured results
        """
        query_embedding = await self.embedding_service.create_embedding(
            query, input_type="query"
        )

        # Convert list to pgvector format string
        embedding_str = "[" + ",".join(map(str, query_embedding)) + "]"

        sql = text(
            """
            SELECT
                ds.id as chunk_id,
                ds.document_id,
                ds.title,
                ds.content,
                d.filename,
                (ds.embedding <#> CAST(:embedding AS vector)) as distance
            FROM document_sections ds
            JOIN documents d ON ds.document_id = d.id
            WHERE d.status = 'completed'
            ORDER BY ds.embedding <#> CAST(:embedding AS vector)
            LIMIT :limit
        """
        )

        result = await self.db.execute(
            sql, {"embedding": embedding_str, "limit": top_k}
        )
        rows = result.fetchall()

        if not rows:
            self._logger.info(
                "Retrieval returned no rows (query=%s)",
                query,
            )
            return RetrievalResponse(query=query, results=[])

        self._logger.info(
            "Retrieval returned %s rows (query=%s)",
            len(rows),
            query,
        )

        results = []
        for row in rows:
            # Convert UUID to string if needed
            chunk_id = str(row.chunk_id) if isinstance(row.chunk_id, UUID) else row.chunk_id
            document_id = str(row.document_id) if isinstance(row.document_id, UUID) else row.document_id

            results.append(
                RetrievalResult(
                    chunk_id=chunk_id,
                    document_id=document_id,
                    title=row.title,
                    content=row.content,
                    source=row.filename,
                    score=float(row.distance),
                )
            )

        return RetrievalResponse(query=query, results=results)
