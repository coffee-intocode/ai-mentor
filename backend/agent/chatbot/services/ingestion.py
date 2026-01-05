"""Document ingestion pipeline for RAG system."""

from pathlib import Path
from typing import List, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Document, DocumentSection
from .embedding import EmbeddingService
from .reducto import ReductoService


class IngestionService:
    """Service for ingesting documents into the RAG system."""

    CHUNK_SIZE = 512
    CHUNK_OVERLAP_PERCENT = 0.15

    def __init__(self, db: AsyncSession, reducto_service: ReductoService):
        """Initialize the ingestion service.

        Args:
            db: Database session
            reducto_service: ReductoService for document parsing
        """
        self.db = db
        self.reducto_service = reducto_service
        self.embedding_service = EmbeddingService()

    async def ingest_document(
        self, file_path: Path, owner_id: int, parse_options: Optional[dict] = None
    ) -> Document:
        """Ingest a document into the RAG system.

        Args:
            file_path: Path to the document file
            owner_id: ID of the user who owns this document
            parse_options: Optional Reducto parsing configurations

        Returns:
            Created Document record with stored job_id for pipelining
        """
        document = Document(
            filename=file_path.name,
            source_path=str(file_path),
            status="processing",
            owner_id=owner_id,
        )
        self.db.add(document)
        await self.db.flush()

        try:
            parsed_content, job_id = await self.reducto_service.parse_document(
                file_path, options=parse_options
            )
            document.reducto_job_id = job_id

            chunks = self._chunk_text(parsed_content)
            await self._create_sections_with_embeddings(document.id, chunks)

            document.status = "completed"
            await self.db.commit()
            return document

        except Exception as e:
            await self.db.rollback()
            raise e

    def _chunk_text(self, text: str) -> List[Tuple[str, str]]:
        """Chunk text into sections with overlap.

        Args:
            text: Full document text

        Returns:
            List of (title, content) tuples
        """
        words = text.split()
        chunks = []
        overlap_size = int(self.CHUNK_SIZE * self.CHUNK_OVERLAP_PERCENT)

        start_idx = 0
        chunk_num = 0

        while start_idx < len(words):
            end_idx = min(start_idx + self.CHUNK_SIZE, len(words))
            chunk_words = words[start_idx:end_idx]
            chunk_text = " ".join(chunk_words)

            title = f"Section {chunk_num + 1}"
            chunks.append((title, chunk_text))

            chunk_num += 1
            start_idx = end_idx - overlap_size

            if end_idx >= len(words):
                break

        return chunks

    async def _create_sections_with_embeddings(
        self, document_id: int, chunks: List[Tuple[str, str]]
    ) -> None:
        """Create document sections with embeddings.

        Args:
            document_id: ID of the parent document
            chunks: List of (title, content) tuples
        """
        contents = [content for _, content in chunks]
        embeddings = await self.embedding_service.create_embeddings(contents)

        for (title, content), embedding in zip(chunks, embeddings):
            section = DocumentSection(
                document_id=document_id,
                title=title,
                content=content,
                embedding=embedding,
            )
            self.db.add(section)

        await self.db.flush()
