```2000
# FastAPI Layered Architecture Guide

## Overview

This project follows FastAPI best practices with a clean, layered architecture pattern that separates concerns and makes the codebase maintainable and scalable.

## Architecture Layers

```

┌─────────────────────────────────────────────────────────────┐
│ API Layer (Routers) │
│ - Handle HTTP requests/responses │
│ - Route definitions and OpenAPI documentation │
│ - Input validation (via Pydantic schemas) │
└──────────────────────┬──────────────────────────────────────┘
│
▼
┌─────────────────────────────────────────────────────────────┐
│ Service Layer (Business Logic) │
│ - Business rules and logic │
│ - Orchestrates multiple repositories │
│ - Exception handling and validation │
└──────────────────────┬──────────────────────────────────────┘
│
▼
┌─────────────────────────────────────────────────────────────┐
│ Repository Layer (Data Access) │
│ - Database operations (CRUD) │
│ - Query construction │
│ - No business logic │
└──────────────────────┬──────────────────────────────────────┘
│
▼
┌─────────────────────────────────────────────────────────────┐
│ Database Layer (ORM Models) │
│ - SQLAlchemy models │
│ - Database schema definition │
│ - Relationships │
└─────────────────────────────────────────────────────────────┘

```

## Project Structure

```

chatbot/
├── **init**.py
├── app.py # Main FastAPI application
├── server.py # Legacy server (to be migrated)
├── config.py # Application configuration
├── database.py # Database connection & session
├── dependencies.py # Dependency injection
├── models.py # SQLAlchemy ORM models
│
├── schemas/ # Pydantic models (Request/Response)
│ ├── **init**.py
│ ├── user.py
│ ├── conversation.py
│ ├── message.py
│ └── chat.py
│
├── repositories/ # Data access layer
│ ├── **init**.py
│ ├── base.py # Base repository with common operations
│ ├── user.py
│ ├── conversation.py
│ └── message.py
│
├── services/ # Business logic layer
│ ├── **init**.py
│ ├── user.py
│ ├── conversation.py
│ ├── message.py
│ └── chat.py
│
└── routers/ # API routes
├── **init**.py
├── users.py
├── conversations.py
├── messages.py
└── chat.py

````

## Layer Responsibilities

### 1. Schemas Layer (`schemas/`)
**Purpose**: Define request/response data structures

- Use **Pydantic models** for validation
- Separate models for create, update, and response
- No business logic
- Type-safe with IDE autocomplete

**Example**:
```python
# schemas/user.py
class UserCreate(BaseModel):
    email: EmailStr
    username: Optional[str] = None

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    username: Optional[str]
    created_at: datetime
````

### 2. Models Layer (`models.py`)

**Purpose**: Define database schema

- **SQLAlchemy ORM models**
- Represent database tables
- Define relationships
- No business logic

**Example**:

```python
# models.py
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
```

### 3. Repositories Layer (`repositories/`)

**Purpose**: Handle database operations

- **CRUD operations only**
- Queries and data access
- No business logic
- Reusable across services

**Example**:

```python
# repositories/user.py
class UserRepository(BaseRepository[User]):
    async def get_by_email(self, email: str) -> Optional[User]:
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()
```

### 4. Services Layer (`services/`)

**Purpose**: Implement business logic

- **Business rules and validation**
- Orchestrate multiple repositories
- Handle exceptions
- Transaction management

**Example**:

```python
# services/user.py
class UserService:
    def __init__(self, db: AsyncSession):
        self.repository = UserRepository(db)

    async def create_user(self, user_data: UserCreate) -> User:
        # Business logic: Check if user exists
        if await self.repository.exists_by_email(user_data.email):
            raise HTTPException(status_code=400, detail="Email exists")

        user = User(email=user_data.email, username=user_data.username)
        return await self.repository.create(user)
```

### 5. Routers Layer (`routers/`)

**Purpose**: Define API endpoints

- **HTTP request handling**
- Route definitions
- Dependency injection
- OpenAPI documentation

**Example**:

```python
# routers/users.py
router = APIRouter(prefix="/users", tags=["users"])

@router.post("/", response_model=UserResponse, status_code=201)
async def create_user(
    user_data: UserCreate,
    service: UserService = Depends(get_user_service)
):
    return await service.create_user(user_data)
```

### 6. Dependencies (`dependencies.py`)

**Purpose**: Dependency injection

- **Service factories**
- Database session management
- Shared dependencies

**Example**:

```python
# dependencies.py
def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    return UserService(db)
```

### 7. Configuration (`config.py`)

**Purpose**: Application settings

- **Environment variables**
- Configuration management
- Using `pydantic-settings`

**Example**:

```python
# config.py
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    app_name: str = "AI Mentor API"
    supabase_database_url: str
    environment: Literal["development", "production"] = "development"
```

## Dependency Flow

```
Request → Router → Service → Repository → Database
            ↓         ↓           ↓
        Schema    Business    SQLAlchemy
                   Logic       Queries
```

### Example Request Flow:

1. **Client** sends POST request to `/api/v1/users`
2. **Router** (`routers/users.py`) receives request
   - Validates input using `UserCreate` schema
   - Injects `UserService` dependency
3. **Service** (`services/user.py`) processes business logic
   - Checks if email already exists
   - Creates User model instance
4. **Repository** (`repositories/user.py`) handles database
   - Executes INSERT query
   - Returns User model
5. **Router** returns response
   - Converts to `UserResponse` schema
   - Serializes to JSON

## Key Principles

### 1. Separation of Concerns

- Each layer has a single responsibility
- Easy to test each layer independently
- Changes in one layer don't affect others

### 2. Dependency Injection

- FastAPI's built-in DI system
- Services and repositories injected automatically
- Easy to mock for testing

### 3. Type Safety

- Full type hints throughout
- IDE autocomplete and error checking
- Pydantic validation at API boundaries

### 4. Testability

- Each layer can be tested independently
- Mock dependencies easily
- Clear interfaces

### 5. Scalability

- Add new features without modifying existing code
- Easy to refactor
- Clear structure for team collaboration

## Benefits

### For Development

- ✅ Clear code organization
- ✅ Easy to find and modify code
- ✅ Reduced code duplication
- ✅ Better team collaboration

### For Maintenance

- ✅ Easy to debug
- ✅ Clear error handling
- ✅ Simple to add new features
- ✅ Refactoring is safer

### For Testing

- ✅ Unit test each layer
- ✅ Mock dependencies easily
- ✅ Integration tests are clearer
- ✅ Better test coverage

### For Performance

- ✅ Async/await throughout
- ✅ Connection pooling
- ✅ Efficient database queries
- ✅ Caching opportunities

## Common Patterns

### 1. Creating Resources

```python
# Router
@router.post("/", response_model=UserResponse, status_code=201)
async def create_user(
    user_data: UserCreate,
    service: UserService = Depends(get_user_service)
):
    return await service.create_user(user_data)

# Service
async def create_user(self, user_data: UserCreate) -> User:
    # Validation
    if await self.repository.exists_by_email(user_data.email):
        raise HTTPException(status_code=400, detail="Exists")

    # Create
    user = User(**user_data.model_dump())
    return await self.repository.create(user)
```

### 2. Getting Resources

```python
# Router
@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    service: UserService = Depends(get_user_service)
):
    return await service.get_user_by_id(user_id)

# Service
async def get_user_by_id(self, user_id: int) -> User:
    user = await self.repository.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Not found")
    return user
```

### 3. Updating Resources

```python
# Router
@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    service: UserService = Depends(get_user_service)
):
    return await service.update_user(user_id, user_data)

# Service
async def update_user(self, user_id: int, user_data: UserUpdate) -> User:
    user = await self.get_user_by_id(user_id)  # Reuse method
    update_data = user_data.model_dump(exclude_unset=True)
    return await self.repository.update(user, **update_data)
```

## Migration from Old Structure

### Before (Old Structure):

```
chatbot/
├── crud.py                    # Mixed concerns
├── example_integration.py     # Monolithic routes
└── models.py
```

### After (New Structure):

```
chatbot/
├── schemas/                   # Pydantic models
├── repositories/              # Data access
├── services/                  # Business logic
├── routers/                   # API routes
├── dependencies.py
└── config.py
```

### Migration Steps:

1. ✅ Create schemas from Pydantic models
2. ✅ Move CRUD to repositories
3. ✅ Extract business logic to services
4. ✅ Create clean routers
5. ✅ Setup dependency injection
6. ✅ Add configuration management
7. ⏳ Update existing endpoints to use new structure

## Running the Application

### Development:

```bash
cd backend/agent

# Using new app structure
uvicorn chatbot.app:app --reload

# Or with the legacy server
uvicorn chatbot.server:app --reload
```

### API Documentation:

- Swagger UI: http://localhost:8080/api/v1/docs
- ReDoc: http://localhost:8080/api/v1/redoc
- OpenAPI JSON: http://localhost:8080/api/v1/openapi.json

## Next Steps

1. **Migrate existing endpoints** from `server.py` to new routers
2. **Add authentication** layer
3. **Implement caching** in services
4. **Add comprehensive tests**
5. **Setup CI/CD** pipeline
6. **Add API versioning** support

## Resources

- [FastAPI Bigger Applications](https://fastapi.tiangolo.com/tutorial/bigger-applications/)
- [FastAPI Dependencies](https://fastapi.tiangolo.com/tutorial/dependencies/)
- [SQLAlchemy 2.0 Docs](https://docs.sqlalchemy.org/en/20/)
- [Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)

```

```
