"""Database configuration and connection setup for Supabase with SQLAlchemy."""

import os
from typing import AsyncGenerator

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

# Load environment variables
load_dotenv()

# Supabase connection URL format: postgresql+asyncpg://user:password@host:port/database
SUPABASE_URL = os.environ.get("SUPABASE_DATABASE_URL")

# Only create engine if database URL is provided
async_engine = None
AsyncSessionLocal = None

if SUPABASE_URL:
    # Create async engine with connection pooling
    async_engine = create_async_engine(
        SUPABASE_URL,
        echo=True,  # Set to False in production
        pool_size=10,
        max_overflow=20,
    )

    # Create async session maker
    AsyncSessionLocal = async_sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=True,  # Automatically flush before queries
    )


# Base class for all models
class Base(DeclarativeBase):
    """Base class for all database models."""

    pass


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency function to get database session for FastAPI."""
    if not AsyncSessionLocal:
        raise RuntimeError(
            "Database not configured. Please set SUPABASE_DATABASE_URL environment variable."
        )

    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize database tables."""
    if not async_engine:
        raise RuntimeError(
            "Database not configured. Please set SUPABASE_DATABASE_URL environment variable."
        )

    async with async_engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
