# Architecture

## Patterns
- **DDD** (Domain-Driven Design) with Bounded Contexts
- **CQRS** (Command Query Responsibility Segregation)
- **Clean Architecture** (layered separation)

## Directory Structure per Bounded Context
```
src/{name}_bc/{subdomain}/
  domain/
    entities.py       # Domain entities with factory methods
    enums.py          # Domain enums
    exceptions.py     # Domain exceptions
    repository.py     # Repository interface (port)
  application/
    commands/          # Command + CommandHandler (same file)
    queries/           # Query + QueryHandler (same file)
    services/          # Application services
    ports.py           # Port interfaces
  infrastructure/
    models.py          # SQLAlchemy models
    repository.py      # Repository implementation
```

## HTTP Layer
```
adapters/http/
  api/{module}/
    routers.py        # FastAPI routers
    controllers.py    # Controllers (use mappers)
    schemas.py        # Pydantic request/response schemas
  middleware/          # Error handler, audit
  schemas/             # Shared schemas
  ws/                  # WebSocket
```

## Framework Base Classes (MANDATORY)
```python
from src.framework.application.command_bus import Command, CommandHandler
from src.framework.application.query_bus import Query, QueryHandler
```

## Data Flow
```
DB Model → Repository → Domain Entity → QueryHandler → DTO → Controller → Response Schema
```

## Key Rules
1. Commands inherit Command, handlers inherit CommandHandler — SAME FILE
2. Queries inherit Query, handlers inherit QueryHandler — SAME FILE
3. Commands return None, queries return DTOs (dataclasses)
4. DTOs contain Value Objects and Enums directly
5. Controllers use explicit Mappers for DTO → Response
6. Routers MUST catch ALL domain exceptions
7. IDs are Value Objects (Ulid subclass), NOT strings
8. Entities have factory methods (.create()), constructor is for hydration only
9. No queries in loops (batch fetch instead)
10. No direct SQL in handlers — use repositories
11. SQLAlchemy 2.0 style: Mapped[str] = mapped_column(String(100))
