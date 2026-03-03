"""add_message_debug_persistence_columns

Revision ID: 7b661154ce6f
Revises: c3f5840a1b2e
Create Date: 2026-03-03
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "7b661154ce6f"
down_revision: Union[str, Sequence[str], None] = "c3f5840a1b2e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "messages",
        sa.Column(
            "parts_json",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=True,
        ),
    )
    op.execute("UPDATE messages SET parts_json = '[]'::jsonb WHERE parts_json IS NULL")
    op.alter_column("messages", "parts_json", nullable=False)

    op.add_column(
        "messages",
        sa.Column("client_message_id", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "messages",
        sa.Column("superseded_by_message_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_messages_superseded_by_message_id_messages",
        "messages",
        "messages",
        ["superseded_by_message_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        op.f("ix_messages_superseded_by_message_id"),
        "messages",
        ["superseded_by_message_id"],
        unique=False,
    )
    op.create_index(
        "ix_messages_conversation_id_created_at",
        "messages",
        ["conversation_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "uq_messages_conversation_id_client_message_id_not_null",
        "messages",
        ["conversation_id", "client_message_id"],
        unique=True,
        postgresql_where=sa.text("client_message_id IS NOT NULL"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(
        "uq_messages_conversation_id_client_message_id_not_null",
        table_name="messages",
    )
    op.drop_index("ix_messages_conversation_id_created_at", table_name="messages")
    op.drop_index(op.f("ix_messages_superseded_by_message_id"), table_name="messages")
    op.drop_constraint(
        "fk_messages_superseded_by_message_id_messages",
        "messages",
        type_="foreignkey",
    )
    op.drop_column("messages", "superseded_by_message_id")
    op.drop_column("messages", "client_message_id")
    op.drop_column("messages", "parts_json")

