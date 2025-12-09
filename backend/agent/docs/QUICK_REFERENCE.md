# Supabase + SQLAlchemy Quick Reference

## 🚀 Initial Setup (One Time)

```bash
# 1. Install dependencies
cd backend/agent
uv sync

# 2. Configure environment
cp env.example .env
# Edit .env with your Supabase credentials

# 3. Create initial migration
uv run alembic revision --autogenerate -m "initial migration"

# 4. Apply migration
uv run alembic upgrade head
```

## 📝 Common Commands

### Migration Commands

```bash
# Create new migration after model changes
uv run alembic revision --autogenerate -m "description"

# Apply all pending migrations
uv run alembic upgrade head

# Rollback last migration
uv run alembic downgrade -1

# View migration history
uv run alembic history

# See current version
uv run alembic current
```

### Database Commands

```bash
# Initialize database (alternative to migrations)
uv run python scripts/init_db.py

# Run FastAPI server
uv run uvicorn chatbot.server:app --reload
```

## 🔌 Connection String Format

### Runtime (async)

```bash
SUPABASE_DATABASE_URL=postgresql+asyncpg://postgres:PASSWORD@PROJECT.supabase.co:5432/postgres
```

### With SSL (production)

```bash
SUPABASE_DATABASE_URL=postgresql+asyncpg://postgres:PASSWORD@PROJECT.supabase.co:5432/postgres?ssl=require
```

## 💻 Code Snippets

### Import Database Session

```python
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from chatbot.database import get_db_session
```

### Create Endpoint with Database

```python
@app.post("/users")
async def create_user(
    email: str,
    db: AsyncSession = Depends(get_db_session)
):
    from chatbot.crud import create_user
    user = await create_user(db, email=email)
    return {"id": user.id, "email": user.email}
```

### Query Database

```python
from sqlalchemy import select
from chatbot.models import User

async def get_all_users(db: AsyncSession):
    result = await db.execute(select(User))
    users = result.scalars().all()
    return users
```

### Create Record

```python
from chatbot.models import User

async def create_user_manual(db: AsyncSession):
    user = User(email="test@example.com", username="test")
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user
```

### Update Record

```python
async def update_user(db: AsyncSession, user_id: int):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user:
        user.username = "new_name"
        await db.commit()
    return user
```

### Delete Record

```python
from sqlalchemy import delete

async def delete_user(db: AsyncSession, user_id: int):
    await db.execute(delete(User).where(User.id == user_id))
    await db.commit()
```

### Filter Records

```python
# Single condition
result = await db.execute(
    select(User).where(User.email == "test@example.com")
)

# Multiple conditions (AND)
result = await db.execute(
    select(User).where(User.email == "test@example.com", User.username == "test")
)

# OR conditions
from sqlalchemy import or_
result = await db.execute(
    select(User).where(or_(User.id == 1, User.id == 2))
)
```

### Join Tables

```python
from sqlalchemy import join

result = await db.execute(
    select(User, Conversation)
    .join(Conversation, User.id == Conversation.user_id)
)
```

### Ordering

```python
# Ascending
result = await db.execute(select(User).order_by(User.created_at))

# Descending
result = await db.execute(select(User).order_by(User.created_at.desc()))
```

### Limit & Offset

```python
# Pagination
result = await db.execute(
    select(User).limit(10).offset(20)
)
```

## 🔧 Model Definition Template

```python
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from chatbot.database import Base

class MyModel(Base):
    """Model description."""
    __tablename__ = "my_table"

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Required field
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    # Optional field
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Indexed field
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )
```

## 📦 CRUD Function Template

```python
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from chatbot.models import MyModel

async def create_item(db: AsyncSession, name: str) -> MyModel:
    """Create a new item."""
    item = MyModel(name=name)
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item

async def get_item_by_id(db: AsyncSession, item_id: int) -> Optional[MyModel]:
    """Get item by ID."""
    result = await db.execute(select(MyModel).where(MyModel.id == item_id))
    return result.scalar_one_or_none()

async def update_item(db: AsyncSession, item_id: int, name: str) -> Optional[MyModel]:
    """Update item."""
    item = await get_item_by_id(db, item_id)
    if item:
        item.name = name
        await db.commit()
        await db.refresh(item)
    return item

async def delete_item(db: AsyncSession, item_id: int) -> bool:
    """Delete item."""
    from sqlalchemy import delete
    result = await db.execute(delete(MyModel).where(MyModel.id == item_id))
    await db.commit()
    return result.rowcount > 0
```

## 🎯 FastAPI Endpoint Template

```python
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from chatbot.database import get_db_session

router = APIRouter(prefix="/api/items")

class ItemCreate(BaseModel):
    name: str

class ItemResponse(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True

@router.post("/", response_model=ItemResponse)
async def create_item_endpoint(
    item: ItemCreate,
    db: AsyncSession = Depends(get_db_session)
):
    """Create new item."""
    from chatbot.crud import create_item
    new_item = await create_item(db, name=item.name)
    return new_item

@router.get("/{item_id}", response_model=ItemResponse)
async def get_item_endpoint(
    item_id: int,
    db: AsyncSession = Depends(get_db_session)
):
    """Get item by ID."""
    from chatbot.crud import get_item_by_id
    item = await get_item_by_id(db, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item
```

## 🐛 Troubleshooting

### Can't connect to database

```bash
# Check environment variable
echo $SUPABASE_DATABASE_URL

# Test connection manually
psql "$SUPABASE_DATABASE_URL"
```

### Migration conflicts

```bash
# Reset migrations (DANGEROUS - only in development)
uv run alembic downgrade base
rm alembic/versions/*.py
uv run alembic revision --autogenerate -m "fresh start"
uv run alembic upgrade head
```

### Import errors

```bash
# Make sure you're in the right directory
cd backend/agent

# Reinstall dependencies
uv sync
```

## 📚 File Locations

- **Models**: `chatbot/models.py`
- **CRUD**: `chatbot/crud.py`
- **Database Config**: `chatbot/database.py`
- **Migrations**: `alembic/versions/`
- **Environment**: `.env` (create from `env.example`)
- **Examples**: `chatbot/example_integration.py`

## 🔗 Useful Links

- [Full Setup Guide](./DATABASE_SETUP.md)
- [Architecture Diagram](./ARCHITECTURE.md)
- [Summary](./SUPABASE_SETUP_SUMMARY.md)
- [SQLAlchemy Docs](https://docs.sqlalchemy.org/en/20/)
- [Supabase Docs](https://supabase.com/docs)

## ⚡ Performance Tips

1. **Use indexes** on frequently queried columns
2. **Limit results** with `.limit()` for large tables
3. **Use connection pooling** (already configured)
4. **Eager load relationships** to avoid N+1 queries
5. **Use async operations** throughout

## 🛡️ Security Reminders

- ✅ Never commit `.env` file
- ✅ Use environment variables for secrets
- ✅ Enable SSL in production (`?ssl=require`)
- ✅ Use parameterized queries (automatic with SQLAlchemy)
- ✅ Validate user input with Pydantic

---

**Need help?** Check [DATABASE_SETUP.md](./DATABASE_SETUP.md) for detailed explanations.
