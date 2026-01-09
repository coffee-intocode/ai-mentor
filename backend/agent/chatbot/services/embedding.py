"""Embedding service for generating vector embeddings using Voyage AI."""

import logging
import os
from typing import List

import voyageai
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

EMBEDDING_TIMEOUT = 30.0  # seconds


class EmbeddingService:
    """Service for creating embeddings using Voyage AI Python SDK."""

    MODEL_NAME = "voyage-3.5-lite"
    EMBEDDING_DIMENSION = 1024
    BATCH_SIZE = 128

    def __init__(self):
        """Initialize the embedding service with AsyncClient."""
        api_key = os.environ.get("VOYAGE_API_KEY")
        if not api_key:
            raise ValueError(
                "VOYAGE_API_KEY environment variable is required for EmbeddingService"
            )
        self.client = voyageai.AsyncClient(api_key=api_key, timeout=EMBEDDING_TIMEOUT)

    async def create_embedding(
        self, text: str, input_type: str = "query"
    ) -> List[float]:
        """Create a single embedding for the given text.

        Args:
            text: The text to embed
            input_type: Type of input - 'query' for search queries, 'document' for documents

        Returns:
            List of floats representing the embedding vector (1024 dimensions)
        """
        logger.info(f"Creating embedding for query, query_length={len(text)}")
        result = await self.client.embed(
            [text], model=self.MODEL_NAME, input_type=input_type
        )
        logger.info("Embedding created successfully")
        return result.embeddings[0]

    async def create_embeddings(
        self, texts: List[str], input_type: str = "document"
    ) -> List[List[float]]:
        """Create embeddings for multiple texts with automatic batching.

        Args:
            texts: List of texts to embed
            input_type: Type of input - 'query' for search queries, 'document' for documents

        Returns:
            List of embedding vectors, one per input text

        Raises:
            Exception: If embedding creation fails
        """
        if not texts:
            return []

        all_embeddings = []

        for i in range(0, len(texts), self.BATCH_SIZE):
            batch = texts[i : i + self.BATCH_SIZE]
            result = await self.client.embed(
                batch, model=self.MODEL_NAME, input_type=input_type
            )
            all_embeddings.extend(result.embeddings)

        return all_embeddings
