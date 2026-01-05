"""Document management API routes."""

from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db_session
from ..dependencies import CurrentUser, get_current_user
from ..models import Document, DocumentSection
from ..services.ingestion import IngestionService
from ..services.reducto import ReductoService

router = APIRouter(
    prefix="/documents",
    tags=["documents"],
    dependencies=[Depends(get_current_user)],
)


class DocumentResponse(BaseModel):
    """Response model for document."""

    id: int
    owner_id: int
    filename: str
    status: str
    section_count: int | None = None

    class Config:
        from_attributes = True


@router.post(
    "/upload",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and ingest a document",
)
async def upload_document(
    current_user: CurrentUser,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db_session),
):
    """Upload and ingest a document into the RAG system."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    # Save uploaded file temporarily
    temp_path = Path(f"/tmp/{file.filename}")
    try:
        with open(temp_path, "wb") as f:
            content = await file.read()
            f.write(content)

        # Ingest the document
        reducto_service = ReductoService(db)
        ingestion_service = IngestionService(db, reducto_service)
        document = await ingestion_service.ingest_document(
            temp_path, owner_id=current_user.local_user_id
        )

        # Count sections
        result = await db.execute(
            select(DocumentSection).where(DocumentSection.document_id == document.id)
        )
        sections = result.scalars().all()

        return DocumentResponse(
            id=document.id,
            owner_id=document.owner_id,
            filename=document.filename,
            status=document.status,
            section_count=len(sections),
        )

    finally:
        # Clean up temp file
        if temp_path.exists():
            temp_path.unlink()


@router.get(
    "",
    response_model=List[DocumentResponse],
    summary="List my documents",
    description="Retrieve all documents for the current user",
)
async def list_documents(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db_session),
):
    """List all ingested documents for the current user."""
    result = await db.execute(
        select(Document).where(Document.owner_id == current_user.local_user_id)
    )
    documents = result.scalars().all()

    response = []
    for doc in documents:
        section_result = await db.execute(
            select(DocumentSection).where(DocumentSection.document_id == doc.id)
        )
        sections = section_result.scalars().all()
        response.append(
            DocumentResponse(
                id=doc.id,
                owner_id=doc.owner_id,
                filename=doc.filename,
                status=doc.status,
                section_count=len(sections),
            )
        )

    return response
