"""Retrieval service for RAG-based document search."""

import logging
from typing import List

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from .embedding import EmbeddingService

logger = logging.getLogger(__name__)


class RetrievalService:
    """Service for retrieving relevant document sections."""

    def __init__(self, db: AsyncSession):
        """Initialize the retrieval service.

        Args:
            db: Database session
        """
        self.db = db
        self.embedding_service = EmbeddingService()

    async def retrieve(self, query: str, top_k: int = 8) -> str:
        """Retrieve relevant document sections based on a query.

        Args:
            query: The search query
            top_k: Number of results to return

        Returns:
            Formatted string with retrieved sections
        """
        logger.info(f"Starting retrieval: query={query[:100]}")
        query_embedding = await self.embedding_service.create_embedding(
            query, input_type="query"
        )
        logger.info("Embedding received, executing vector search")

        # Convert list to pgvector format string
        embedding_str = "[" + ",".join(map(str, query_embedding)) + "]"

        sql = text(
            """
            SELECT 
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
            return "No relevant documents found."

        formatted_results = []
        for row in rows:
            formatted_results.append(
                f"# {row.title}\n"
                f"Source: {row.filename}\n"
                f"Distance: {row.distance:.4f}\n\n"
                f"{row.content}\n"
            )

        return "\n\n---\n\n".join(formatted_results)
