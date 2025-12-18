"""add_pgvector_and_document_tables

Revision ID: dfb60e1f20bf
Revises: a2284347cd88
Create Date: 2025-12-12 06:52:25.039922

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision: str = "dfb60e1f20bf"
down_revision: Union[str, Sequence[str], None] = "a2284347cd88"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("CREATE SCHEMA IF NOT EXISTS extensions;")
    op.execute("CREATE EXTENSION IF NOT EXISTS vector WITH SCHEMA extensions;")

    op.create_table(
        "documents",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("filename", sa.String(length=500), nullable=False),
        sa.Column("source_path", sa.String(length=1000), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("reducto_job_id", sa.String(length=255), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "document_sections",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("document_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("embedding", Vector(1024), nullable=False),
        sa.ForeignKeyConstraint(
            ["document_id"],
            ["documents.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_document_sections_document_id"),
        "document_sections",
        ["document_id"],
        unique=False,
    )

    op.execute(
        """
        CREATE INDEX idx_document_sections_embedding 
        ON document_sections 
        USING hnsw (embedding vector_ip_ops)
        WITH (m = 16, ef_construction = 64);
    """
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP INDEX IF EXISTS idx_document_sections_embedding;")
    op.drop_index(
        op.f("ix_document_sections_document_id"), table_name="document_sections"
    )
    op.drop_table("document_sections")
    op.drop_table("documents")
    op.execute("DROP EXTENSION IF EXISTS vector CASCADE;")
