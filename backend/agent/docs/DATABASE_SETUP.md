# Supabase with SQLAlchemy Setup Guide

This guide explains how to set up and use Supabase with SQLAlchemy in this project.

## Overview

The application uses:

- **Supabase**: PostgreSQL database as a service
- **SQLAlchemy 2.0**: ORM with async support
- **asyncpg**: Async PostgreSQL driver for runtime
- **psycopg2**: Sync PostgreSQL driver for migrations
- **Alembic**: Database migration tool

## Getting Your Supabase Connection String

1. Go to your [Supabase Dashboard](https://app.supabase.com/)
2. Select your project
3. Navigate to **Settings** → **Database**
4. Find **Connection string** section
5. Select **URI** tab
6. Copy the connection string (it looks like: `postgresql://postgres:[YOUR-PASSWORD]@[PROJECT-REF].supabase.co:5432/postgres`)

## Environment Setup

1. Copy the environment template:

```bash
cp env.example .env
```

2. Edit `.env` and update the connection string:

```bash
# Replace with your actual Supabase connection string
SUPABASE_DATABASE_URL=postgresql+asyncpg://postgres:your-password@your-project.supabase.co:5432/postgres
```

**Important**: For async operations (runtime), use `postgresql+asyncpg://`. Alembic will automatically convert this to `postgresql://` for migrations.

## Installing Dependencies

Install all required dependencies:

```bash
uv sync
```

## Database Models

The application includes three models in `chatbot/models.py`:

1. **User**: Stores user information
2. **Conversation**: Stores chat conversations
3. **Message**: Stores individual messages in conversations

## Database Migrations

### Creating a New Migration

After creating or modifying models, generate a migration:

```bash
uv run alembic revision --autogenerate -m "description of changes"
```

### Applying Migrations

Apply migrations to your database:

```bash
uv run alembic upgrade head
```

### Downgrading Migrations

Rollback the last migration:

```bash
uv run alembic downgrade -1
```

### Viewing Migration History

```bash
uv run alembic history
```

## Using the Database in Your Application

### Getting a Database Session

In FastAPI endpoints:

```python
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from chatbot.database import get_db_session

@app.get("/users")
async def get_users(db: AsyncSession = Depends(get_db_session)):
    result = await db.execute(select(User))
    users = result.scalars().all()
    return users
```

### Creating Records

```python
from chatbot.models import User

async def create_user(db: AsyncSession, email: str, username: str):
    new_user = User(email=email, username=username)
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user
```

### Querying Records

```python
from sqlalchemy import select
from chatbot.models import User

async def get_user_by_email(db: AsyncSession, email: str):
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()
```

### Updating Records

```python
async def update_user(db: AsyncSession, user_id: int, username: str):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user:
        user.username = username
        await db.commit()
        await db.refresh(user)
    return user
```

### Deleting Records

```python
from sqlalchemy import delete

async def delete_user(db: AsyncSession, user_id: int):
    await db.execute(delete(User).where(User.id == user_id))
    await db.commit()
```

## Troubleshooting

### Connection Issues

If you can't connect to Supabase:

1. Verify your connection string is correct
2. Check that your IP is allowed in Supabase settings
3. Ensure you're using the correct password

### Migration Issues

If migrations fail:

1. Check that your `SUPABASE_DATABASE_URL` is set correctly
2. Verify you have network access to Supabase
3. Make sure all model imports are correct in `alembic/env.py`

### SSL Certificate Issues

If you encounter SSL errors, you may need to add SSL mode to your connection string:

```bash
SUPABASE_DATABASE_URL=postgresql+asyncpg://postgres:password@host:5432/postgres?ssl=require
```

## Best Practices

1. **Always use migrations**: Don't modify the database schema directly
2. **Use async operations**: Take advantage of async/await for better performance
3. **Handle transactions**: Use the provided `get_db_session` dependency for automatic transaction management
4. **Index frequently queried fields**: Add indexes to columns used in WHERE clauses
5. **Use connection pooling**: The engine is configured with connection pooling by default

## Additional Resources

- [SQLAlchemy 2.0 Documentation](https://docs.sqlalchemy.org/en/20/)
- [Supabase Documentation](https://supabase.com/docs)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [asyncpg Documentation](https://magicstack.github.io/asyncpg/)
