# Application Layer (CQRS)

Complete guide to Queries, Commands, Events, and Handlers in the Application layer.

## Overview

The Application Layer implements **CQRS** (Command Query Responsibility Segregation):
- **Commands**: Write operations (return `None`)
- **Queries**: Read operations (return DTOs)
- **Events**: Domain event handlers

---

## Queries (Read Operations)

### Query Structure

**IMPORTANT:** Query and QueryHandler are in the **SAME FILE**.

**File location:** `application/queries/get_candidate_by_id.py`

```python
from dataclasses import dataclass
from typing import Optional
from src.framework.application.query_bus import Query, QueryHandler

# Query and Handler in the SAME FILE
@dataclass
class GetCandidateByIdQuery(Query):
    """Query to get a candidate by ID"""
    id: CandidateId  # Use ValueObject, not string


class GetCandidateByIdQueryHandler(QueryHandler[GetCandidateByIdQuery, Optional[CandidateDto]]):
    """Handler for GetCandidateByIdQuery"""

    def __init__(self, candidate_repository: CandidateRepositoryInterface):
        self.candidate_repository = candidate_repository

    def handle(self, query: GetCandidateByIdQuery) -> Optional[CandidateDto]:
        candidate = self.candidate_repository.get_by_id(query.id)
        if candidate:
            return CandidateDtoMapper.from_model(candidate)
        return None
```

### Important Rules

1. **All queries must inherit from `Query`**
2. **All handlers must inherit from `QueryHandler[TQuery, TResult]`**
3. **Query and Handler in the SAME FILE**
4. **Handlers are stateless** - All dependencies injected via `__init__`
5. **Queries return DTOs** - Never return entities
6. **Use DtoMapper** - `CandidateDtoMapper.from_model(entity)` to convert entity to DTO

### Query Return Types (Allowed)

✅ Allowed returns:
- DTO directly (`CandidateDto`)
- Optional DTO (`Optional[CandidateDto]`)
- List of DTOs (`List[CandidateDto]`)
- Primitives (`int`, `str`, `bool`, `float`)

❌ Not allowed:
- Entities (use DTOs instead)
- SQLAlchemy models
- Complex mutable objects

### DTOs Can Have Methods

#### ✅ Allowed - Decorating Data:
```python
@dataclass
class CandidateDto:
    id: str
    first_name: str
    last_name: str
    created_at: datetime

    @property
    def full_name(self) -> str:
        """Decoration - combines data"""
        return f"{self.first_name} {self.last_name}"

    def created_at_formatted(self) -> str:
        """Decoration - formats date"""
        return self.created_at.strftime("%Y-%m-%d %H:%M")
```

#### ❌ Not Allowed - Business Rules:
```python
@dataclass
class CandidateDto:
    status: str

    def is_eligible_for_interview(self) -> bool:
        # WRONG: Business rule belongs in Entity
        return self.status == "ACTIVE"
```

**Rule:** DTOs can format/decorate data, but cannot contain business logic.

### Query Naming Conventions

#### Verbs:

**Get** - Always expects to find, raises error if not found
```python
GetCandidateByIdQuery          # Raises CandidateNotFoundException if not found
GetInterviewByIdQuery          # Raises InterviewNotFoundException
```

**Find** - May or may not find element
```python
FindCandidatesByStatusQuery    # Returns empty list if none found
FindInterviewByDateQuery       # Returns None if not found
```

**List** - Returns collection (usually paginated)
```python
ListCandidatesQuery            # Returns paginated list
ListInterviewsQuery            # Returns paginated list
```

**Search** - For filtered searches with complex criteria
```python
SearchCandidatesQuery          # With filters, pagination
SearchJobPositionsQuery        # Complex search criteria
```

#### Suffixes:

**Dto** - Returns single DTO with standard data
```python
GetCandidateByIdQuery -> CandidateDto
```

**FullDto** - Returns DTO with all relations
```python
GetCandidateFullQuery -> CandidateFullDto
# Includes: interviews, comments, documents, etc.
```

**RefDto** - Returns minimal reference DTO
```python
GetCandidateRefQuery -> CandidateRefDto
# Only: id, name, email (minimal fields)
```

### Performance Rules

#### ❌ Forbidden: Queries in Loops

**Bad Example:**
```python
for candidate in candidates:
    interviews = self.query_bus.query(
        GetInterviewsByCandidateIdQuery(candidate.id)
    )
    # WRONG: N queries
```

**Good Example:**
```python
# 1. Get all candidate IDs
candidate_ids = [c.id for c in candidates]

# 2. Get all interviews in ONE query
all_interviews = self.query_bus.query(
    GetInterviewsByCandidateIdsQuery(candidate_ids)  # Single query with IN clause
)

# 3. Join in Python
interviews_by_candidate = {}
for interview in all_interviews:
    if interview.candidate_id not in interviews_by_candidate:
        interviews_by_candidate[interview.candidate_id] = []
    interviews_by_candidate[interview.candidate_id].append(interview)

for candidate in candidates:
    candidate.interviews = interviews_by_candidate.get(candidate.id, [])
```

---

## Commands (Write Operations)

### Command Structure

**IMPORTANT:** Command and CommandHandler are in the **SAME FILE**.

**File location:** `application/commands/create_candidate.py`

```python
from dataclasses import dataclass
from src.framework.application.command_bus import Command, CommandHandler

# Command and Handler in the SAME FILE
@dataclass
class CreateCandidateCommand(Command):
    """Command to create a new candidate"""
    id: CandidateId  # ID passed as ValueObject
    name: str
    email: str


class CreateCandidateCommandHandler(CommandHandler[CreateCandidateCommand]):
    """Handler for CreateCandidateCommand"""

    def __init__(
        self,
        candidate_repository: CandidateRepositoryInterface,
        event_bus: EventBus
    ):
        self.candidate_repository = candidate_repository
        self.event_bus = event_bus

    def execute(self, command: CreateCandidateCommand) -> None:  # Returns None
        # 1. Create entity via factory method
        candidate = Candidate.create(
            id=command.id,
            name=command.name,
            email=command.email
        )

        # 2. Persist
        self.candidate_repository.save(candidate)

        # 3. Publish events
        self.event_bus.publish(candidate.pull_domain_events())

        # NO RETURN - Commands return None
```

### Command Rules

**CRITICAL:**
- Commands **NEVER return anything** - return type is `None`
- Commands can **ONLY raise exceptions** for errors
- **Command and Handler in the SAME FILE**
- **ID is generated BEFORE the command** and passed as ValueObject
- Commands should be **imperative** (CreateCandidate, UpdateInterview)
- Handlers should be **stateless**
- Commands should contain **only data** (no logic)
- Business logic belongs in **Entity** or **Domain Service**

### Usage Pattern in Controller

```python
class CandidateController:
    def create_candidate(self, request: CreateCandidateRequest) -> CandidateResponse:
        # 1. Generate ID BEFORE command (as ValueObject)
        candidate_id = CandidateId.generate()

        # 2. Execute command (returns None)
        self.command_bus.execute(
            CreateCandidateCommand(
                id=candidate_id,  # Pass ValueObject, not string
                name=request.name,
                email=request.email
            )
        )

        # 3. Query to get the created entity
        dto = self.query_bus.query(
            GetCandidateByIdQuery(id=candidate_id)
        )

        # 4. Return via explicit Mapper
        return CandidateMapper.dto_to_response(dto)
```

### Command Handler Checklist

- [ ] Command and Handler in SAME FILE
- [ ] Handler inherits from `CommandHandler[TCommand]`
- [ ] `execute` method returns `None`
- [ ] ID received from command as ValueObject (not generated in handler)
- [ ] Uses repository for data access
- [ ] Publishes domain events if needed
- [ ] No return statement

---

## DTOs (Data Transfer Objects)

### DTO Location

DTOs are located in: `application/queries/shared/`

### DTO Structure

**IMPORTANT:** DTOs are `@dataclass` and contain domain Value Objects and Enums directly. They are NOT Pydantic models.

```python
from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime

@dataclass
class CandidateDto:
    """DTO for candidate data - contains Value Objects directly"""
    id: CandidateId                    # ValueObject, NOT string
    name: str
    email: str
    status: CandidateStatusEnum        # Enum directly, NOT string
    created_at: datetime
    updated_at: Optional[datetime] = None

    @classmethod
    def from_entity(cls, entity: Candidate) -> "CandidateDto":
        """Create DTO from domain entity"""
        return cls(
            id=entity.id,              # Keep as ValueObject
            name=entity.name,
            email=entity.email,
            status=entity.status,      # Keep as Enum
            created_at=entity.created_at,
            updated_at=entity.updated_at
        )
```

### DtoMapper Pattern

DTOs should have a corresponding Mapper class for entity → DTO conversion:

**File location:** `application/queries/shared/candidate_dto_mapper.py`

```python
class CandidateDtoMapper:
    @staticmethod
    def from_model(candidate: Candidate) -> CandidateDto:
        return CandidateDto(
            id=candidate.id,
            name=candidate.name,
            email=candidate.email,
            status=candidate.status,
            created_at=candidate.created_at,
            updated_at=candidate.updated_at
        )
```

### DTO Rules

1. **DTOs are dataclasses** - Use `@dataclass` decorator
2. **DTOs contain Value Objects** - `CandidateId`, `CompanyId`, etc. (NOT strings)
3. **DTOs contain Enums directly** - `CandidateStatusEnum` (NOT `.value`)
4. **DTOs have DtoMapper** - Separate mapper class for entity → DTO
5. **Presentation Mapper handles serialization** - Explicit conversion to primitives

### Full DTO Example

```python
@dataclass
class CandidateFullDto:
    """Full DTO with all relations"""
    id: str
    name: str
    email: str
    status: str
    interviews: List["InterviewDto"]
    comments: List["CommentDto"]
    created_at: datetime

    @classmethod
    def from_entity(
        cls,
        entity: Candidate,
        interviews: List[Interview],
        comments: List[Comment]
    ) -> "CandidateFullDto":
        return cls(
            id=str(entity.id),
            name=entity.name,
            email=entity.email,
            status=entity.status.value,
            interviews=[InterviewDto.from_entity(i) for i in interviews],
            comments=[CommentDto.from_entity(c) for c in comments],
            created_at=entity.created_at
        )
```

---

## Event Handlers

### Event Handler Structure

```python
from src.framework.application.event_handler import EventHandler

class OnCandidateCreatedSendWelcomeEmail(EventHandler[CandidateCreatedEvent]):
    """Send welcome email when candidate is created"""

    def __init__(self, email_service: EmailServiceInterface):
        self.email_service = email_service

    def handle(self, event: CandidateCreatedEvent) -> None:
        self.email_service.send_welcome_email(
            email=event.email,
            name=event.name
        )
```

### Event Content Best Practices

#### ❌ Wrong: Only store ID
```python
@dataclass
class CandidateUpdatedEvent:
    candidate_id: str  # Consumer has to fetch everything
```

#### ❌ Wrong: Store everything
```python
@dataclass
class CandidateUpdatedEvent:
    candidate: Candidate  # Too much coupling
    old_data: dict
    new_data: dict
```

#### ✅ Correct: Store relevant data
```python
@dataclass
class CandidateEmailUpdatedEvent:
    candidate_id: str
    old_email: Optional[str]
    new_email: str
```

### Event Handler Best Practices

1. **Always read latest data from DB** - Don't trust event data for current state
2. **Keep event payload small** - Only include what's needed
3. **Separate events by purpose** - `CandidateEmailUpdated` vs `CandidateNameUpdated`
4. **Handlers should be idempotent** - Safe to run multiple times

---

## Handler Registration

Handlers must be registered in the dependency injection container:

```python
# core/containers/candidate_container.py
from dependency_injector import containers, providers

class CandidateContainer(containers.DeclarativeContainer):
    # Query Handlers
    get_candidate_by_id_query_handler = providers.Factory(
        GetCandidateByIdQueryHandler,
        repository=candidate_repository
    )

    # Command Handlers
    create_candidate_command_handler = providers.Factory(
        CreateCandidateCommandHandler,
        repository=candidate_repository,
        event_bus=event_bus
    )
```

---

**See also:**
- [Architecture](architecture.md) - BC communication
- [Infrastructure](infrastructure.md) - Repositories
- [Critical Rules](critical-rules.md) - Performance and CQRS rules
- [Code Quality](code-quality.md) - SOLID principles
