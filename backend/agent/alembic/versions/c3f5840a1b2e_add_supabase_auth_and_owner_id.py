"""add_supabase_auth_and_owner_id

Revision ID: c3f5840a1b2e
Revises: dfb60e1f20bf
Create Date: 2025-01-04

This migration adds:
- supabase_user_id to users table for Supabase auth integration
- Renames user_id to owner_id on conversations table
- Adds owner_id FK to messages table
- Adds owner_id FK to documents table
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c3f5840a1b2e"
down_revision: Union[str, Sequence[str], None] = "dfb60e1f20bf"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1. Add supabase_user_id to users table
    op.add_column(
        "users",
        sa.Column("supabase_user_id", sa.String(36), nullable=True),
    )
    op.create_index(
        op.f("ix_users_supabase_user_id"),
        "users",
        ["supabase_user_id"],
        unique=True,
    )

    # 2. Rename user_id to owner_id on conversations and add FK
    op.alter_column("conversations", "user_id", new_column_name="owner_id")
    op.drop_index("ix_conversations_user_id", table_name="conversations")
    op.create_index(
        op.f("ix_conversations_owner_id"),
        "conversations",
        ["owner_id"],
        unique=False,
    )
    op.create_foreign_key(
        "fk_conversations_owner_id_users",
        "conversations",
        "users",
        ["owner_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # 3. Add owner_id to messages table
    # First add as nullable, then we'll need to backfill if there's existing data
    op.add_column(
        "messages",
        sa.Column("owner_id", sa.Integer(), nullable=True),
    )
    # Backfill owner_id from conversation's owner_id
    op.execute(
        """
        UPDATE messages m
        SET owner_id = c.owner_id
        FROM conversations c
        WHERE m.conversation_id = c.id
        """
    )
    # Now make it NOT NULL and add FK
    op.alter_column("messages", "owner_id", nullable=False)
    op.create_index(
        op.f("ix_messages_owner_id"),
        "messages",
        ["owner_id"],
        unique=False,
    )
    op.create_foreign_key(
        "fk_messages_owner_id_users",
        "messages",
        "users",
        ["owner_id"],
        ["id"],
        ondelete="CASCADE",
    )
    # Also add FK for conversation_id
    op.create_foreign_key(
        "fk_messages_conversation_id_conversations",
        "messages",
        "conversations",
        ["conversation_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # 4. Add owner_id to documents table
    op.add_column(
        "documents",
        sa.Column("owner_id", sa.Integer(), nullable=True),
    )
    # For existing documents without owner, we'll need to handle this manually
    # or delete orphaned documents. For now, we'll make it nullable initially.
    # In production, you'd want to backfill or clean up first.
    op.create_index(
        op.f("ix_documents_owner_id"),
        "documents",
        ["owner_id"],
        unique=False,
    )
    op.create_foreign_key(
        "fk_documents_owner_id_users",
        "documents",
        "users",
        ["owner_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    """Downgrade schema."""
    # 4. Remove owner_id from documents
    op.drop_constraint("fk_documents_owner_id_users", "documents", type_="foreignkey")
    op.drop_index(op.f("ix_documents_owner_id"), table_name="documents")
    op.drop_column("documents", "owner_id")

    # 3. Remove owner_id from messages
    op.drop_constraint(
        "fk_messages_conversation_id_conversations", "messages", type_="foreignkey"
    )
    op.drop_constraint("fk_messages_owner_id_users", "messages", type_="foreignkey")
    op.drop_index(op.f("ix_messages_owner_id"), table_name="messages")
    op.drop_column("messages", "owner_id")

    # 2. Rename owner_id back to user_id on conversations
    op.drop_constraint(
        "fk_conversations_owner_id_users", "conversations", type_="foreignkey"
    )
    op.drop_index(op.f("ix_conversations_owner_id"), table_name="conversations")
    op.alter_column("conversations", "owner_id", new_column_name="user_id")
    op.create_index("ix_conversations_user_id", "conversations", ["user_id"])

    # 1. Remove supabase_user_id from users
    op.drop_index(op.f("ix_users_supabase_user_id"), table_name="users")
    op.drop_column("users", "supabase_user_id")
