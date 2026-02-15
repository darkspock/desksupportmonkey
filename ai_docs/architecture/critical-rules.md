# Critical Rules - MUST READ

**READ THIS FIRST BEFORE ANY TASK**

These are non-negotiable rules that prevent critical errors in production.

---

## MOST CRITICAL RULES (TOP 6)

### #0: Routers MUST Catch ALL Domain Exceptions

**CRITICAL:** Every router endpoint MUST catch all domain exceptions and return proper HTTP errors.

**❌ FORBIDDEN:**
```python
@router.post("/register")
async def register(request: RegisterRequest, controller: AuthController):
    # WRONG: WeakPasswordException not caught → 500 Internal Server Error
    return controller.register(request)
```

**✅ CORRECT:**
```python
@router.post("/register")
async def register(request: RegisterRequest, controller: AuthController):
    try:
        return controller.register(request)
    except UserAlreadyExistsException as e:
        raise HTTPException(status_code=409, detail=str(e))
    except WeakPasswordException as e:
        raise HTTPException(status_code=422, detail=str(e))
    # Catch ALL possible domain exceptions
```

**Why this is critical:**
- Uncaught exceptions return 500 with no useful message
- Frontend cannot display helpful error to user
- Backend implementation details leak to client
- Contract tests will fail

**Rules:**
- List ALL domain exceptions that can be thrown by the handler
- Map each exception to appropriate HTTP status code
- Use `str(e)` for user-friendly messages
- Write contract tests to verify error responses
- Run `make test-contract` before deploy

**See also:** [HTTP Layer - Error Handling](http-layer.md#error-handling)

---

### #1: Commands MUST Inherit from Base Classes

**CRITICAL:** All Commands, Queries, and their Handlers MUST inherit from base classes. This is MANDATORY for the CommandBus and QueryBus to work correctly.

**❌ FORBIDDEN:**
```python
# Missing inheritance
class CreateCandidateCommand:
    candidate_id: str
    name: str

class CreateCandidateCommandHandler:
    def execute(self, command):
        pass
```

**✅ CORRECT:**
```python
from dataclasses import dataclass
from src.framework.application.command_bus import Command, CommandHandler

@dataclass
class CreateCandidateCommand(Command):  # MUST inherit from Command
    candidate_id: str
    name: str

class CreateCandidateCommandHandler(CommandHandler[CreateCandidateCommand]):  # MUST inherit
    def execute(self, command: CreateCandidateCommand) -> None:  # Returns None
        pass
```

**Rules:**
- ALL Commands MUST inherit from `Command` base class
- ALL CommandHandlers MUST inherit from `CommandHandler[TCommand]`
- CommandHandler's `execute` method MUST return `None`
- Commands are used for write operations and side effects
- **Command and Handler MUST be in the SAME FILE**

---

### #2: Queries MUST Return DTOs, NOT Entities

**IMPORTANT:** Query and QueryHandler are in the SAME FILE.

**❌ FORBIDDEN:**
```python
class GetCandidateByIdQueryHandler(QueryHandler[GetCandidateByIdQuery, Candidate]):
    def handle(self, query: GetCandidateByIdQuery) -> Candidate:  # WRONG: Returns Entity
        return self.repository.get_by_id(query.candidate_id)
```

**✅ CORRECT:**
```python
from dataclasses import dataclass
from src.framework.application.query_bus import Query, QueryHandler

@dataclass
class GetCandidateByIdQuery(Query):  # MUST inherit from Query
    candidate_id: str

class GetCandidateByIdQueryHandler(QueryHandler[GetCandidateByIdQuery, CandidateDto]):
    def handle(self, query: GetCandidateByIdQuery) -> CandidateDto:  # Returns DTO
        entity = self.repository.get_by_id(query.candidate_id)
        return CandidateDto.from_entity(entity)
```

**Rules:**
- ALL Queries MUST inherit from `Query` base class
- ALL QueryHandlers MUST inherit from `QueryHandler[TQuery, TResult]`
- QueryHandler's `handle` method MUST return DTOs (or List[DTO], Optional[DTO])
- Queries are used for read operations only
- **Query and Handler MUST be in the SAME FILE**

---

### DTOs Are Dataclasses with Value Objects

**IMPORTANT:** DTOs are `@dataclass`, NOT Pydantic models. They contain domain Value Objects and Enums directly.

```python
from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class CandidateDto:
    id: CandidateId           # ValueObject, NOT string
    name: str
    status: CandidateStatusEnum  # Enum directly
    created_at: datetime

    @classmethod
    def from_entity(cls, entity: Candidate) -> 'CandidateDto':
        return cls(
            id=entity.id,
            name=entity.name,
            status=entity.status,
            created_at=entity.created_at
        )
```

**Rules:**
- DTOs are Python dataclasses (`@dataclass`)
- DTOs can contain Value Objects (CandidateId, CompanyId, etc.)
- DTOs can contain Enums directly
- DTOs have `from_entity()` factory method
- Mappers handle DTO → Response conversion (explicit)

---

### #3: Controllers MUST Use Mappers for DTO → Response

**❌ FORBIDDEN:**
```python
# In controller - implicit conversion
def get_candidate(self, candidate_id: str) -> CandidateResponse:
    dto = self.query_bus.query(query)
    return CandidateResponse.model_validate(dto)  # WRONG: Magic/implicit
```

**✅ CORRECT:**
```python
# In controller - explicit Mapper
def get_candidate(self, candidate_id: str) -> CandidateResponse:
    dto = self.query_bus.query(query)
    return CandidateMapper.dto_to_response(dto)  # CORRECT: Explicit conversion
```

**Mapper Structure:**
```python
# presentation/mappers/candidate_mapper.py
class CandidateMapper:
    @staticmethod
    def dto_to_response(dto: CandidateDto) -> CandidateResponse:
        return CandidateResponse(
            id=str(dto.id.value),
            name=dto.name,
            status=dto.status.value,
            created_at=dto.created_at.isoformat()
        )
```

**Response Schema (simple, no magic):**
```python
class CandidateResponse(BaseModel):
    id: str
    name: str
    status: str
    created_at: str
```

**Rules:**
- Controllers MUST use `Mapper.dto_to_response(dto)` for conversion
- Mappers are in `presentation/mappers/`
- Response schemas are simple (no field_validators)
- Explicit is better than implicit

---

### #4: Commands NEVER Return Values

**Commands in CQRS ALWAYS return `None`** - They can ONLY raise exceptions.

**❌ FORBIDDEN:**
```python
# WRONG: Expecting command to return value
candidate_id = self.command_bus.execute(
    CreateCandidateCommand(data)
)
```

**✅ CORRECT:**
```python
# Generate ID first, pass to command
candidate_id = CandidateId.generate()

self.command_bus.execute(
    CreateCandidateCommand(
        candidate_id=candidate_id,  # ID passed in
        name="John Doe",
        email="john@example.com"
    )
)

# Use the already-generated candidate_id for subsequent operations
candidate = self.query_bus.query(GetCandidateByIdQuery(candidate_id))
```

---

### #5: NEVER Execute Queries in Loops

**PostgreSQL database can grow large** - Always analyze performance impact.

**❌ FORBIDDEN:**
```python
for candidate in candidates:
    # WRONG: N queries in loop
    interviews = self.interview_repository.find_by_candidate_id(candidate.id)
```

**✅ CORRECT:**
```python
# 1. Get all candidate IDs
candidate_ids = [c.id for c in candidates]

# 2. Get all interviews in ONE query
all_interviews = self.interview_repository.find_by_candidate_ids(candidate_ids)

# 3. Join in Python
for candidate in candidates:
    candidate.interviews = [i for i in all_interviews if i.candidate_id == candidate.id]
```

---

## Data Flow Rules

### Strict Transformation Chain

```
Database Model → Repository → Domain Entity → Query Handler → DTO → Controller → Response Schema
```

**Repository Layer:**
- Input: Database Model (SQLAlchemy)
- Output: Domain Entity
- Responsibility: Convert models to entities and vice versa

**Query Handler Layer:**
- Input: Domain Entity (from repository)
- Output: DTO
- Responsibility: Convert entities to DTOs

**Controller Layer:**
- Input: DTO (from query handler)
- Output: Response Schema (Pydantic)
- Responsibility: Use Mappers for DTO → Response conversion

### Forbidden Direct Dependencies

- ❌ Controllers MUST NOT directly access repositories
- ❌ Handlers MUST NOT directly access SQLAlchemy models
- ❌ Controllers MUST NOT directly access domain entities
- ❌ DTOs MUST NOT be used in domain layer
- ❌ Controllers MUST NOT return DTOs directly

---

## Entity Factory Methods

### Entities MUST Have Factory Methods

**❌ FORBIDDEN:**
```python
class Candidate:
    def __init__(self, id, name, email, status):
        self.id = id
        self.name = name
        self.email = email
        self.status = status  # No validation!
```

**✅ CORRECT:**
```python
class Candidate:
    def __init__(self, id: CandidateId, name: str, email: str, status: CandidateStatus):
        # Constructor only for repository hydration
        self._id = id
        self._name = name
        self._email = email
        self._status = status

    @classmethod
    def create(cls, name: str, email: str) -> "Candidate":
        """Factory method for creating new candidates"""
        # Validation and business logic here
        if not email or "@" not in email:
            raise InvalidEmailError(email)

        return cls(
            id=CandidateId.generate(),
            name=name,
            email=email,
            status=CandidateStatus.PENDING
        )

    def update_details(self, name: str, email: str) -> None:
        """Update method with validation"""
        if not email or "@" not in email:
            raise InvalidEmailError(email)
        self._name = name
        self._email = email
```

**Rules:**
- Constructor is ONLY for repository hydration
- Factory methods (`create()`) for new entity creation
- Update methods (`update_details()`) for modifications
- Status changes through specific methods (not direct assignment)

---

## Handler Rules

### Handlers NEVER Use Direct SQL

**❌ FORBIDDEN:**
```python
class GetCandidateHandler:
    def handle(self, query):
        # WRONG: Direct SQL in handler
        result = self.session.execute(
            text("SELECT * FROM candidates WHERE id = :id"),
            {"id": query.candidate_id}
        )
```

**✅ CORRECT:**
```python
class GetCandidateHandler:
    def __init__(self, repository: CandidateRepositoryInterface):
        self.repository = repository

    def handle(self, query):
        # Use repository
        return self.repository.get_by_id(query.candidate_id)
```

**Rules:**
- ❌ NEVER access database directly in Handlers
- ✅ ALWAYS use Repository interfaces
- ✅ SQL only allowed in Infrastructure layer (Repository implementations)

---

## Value Objects

### IDs Are Value Objects, NOT Strings

**❌ FORBIDDEN:**
```python
def get_candidate(self, candidate_id: str) -> Candidate:  # WRONG: string ID
    pass
```

**✅ CORRECT:**
```python
from src.framework.domain.value_objects import Ulid

class CandidateId(Ulid):
    pass

def get_candidate(self, candidate_id: CandidateId) -> Candidate:  # Correct: ValueObject
    pass
```

**Rules:**
- ❌ NEVER use `str` for IDs in interfaces/parameters
- ✅ ALWAYS use ValueObjects (`CandidateId`, `CompanyId`, etc.)
- ✅ In Repository implementation: use `.value` to get string

---

## Development Environment

### Use Makefile Commands

**✅ CORRECT:**
```bash
make mypy      # Type checking
make test      # Run tests
make migrate   # Run migrations
make linter    # Run linter
```

**❌ WRONG:**
```bash
docker-compose exec web mypy ...  # Don't use docker directly
python -m mypy ...                 # Don't run Python directly
```

---

## Quick Checklist Before Starting Any Task

### For ALL Tasks
- [ ] Read Critical Rules (this file)
- [ ] Understand the DDD architecture
- [ ] Check if performance impact on PostgreSQL

### For Frontend-Backend Features (MANDATORY)
- [ ] **API contract defined FIRST** in `/docs/api-contracts/`
- [ ] **Contract tests written BEFORE implementation**
- [ ] **Router catches ALL domain exceptions (no 500 errors!)**
- [ ] **`make test-contract` passes before finishing**

See [Development Workflow](development-workflow.md) for CONTRACT-FIRST process.

### For Backend Implementation
- [ ] Commands inherit from `Command`, handlers from `CommandHandler`
- [ ] Queries inherit from `Query`, handlers from `QueryHandler`
- [ ] **Command + Handler in SAME file**
- [ ] **Query + Handler in SAME file**
- [ ] Commands return `None`, Queries return DTOs (dataclasses)
- [ ] DTOs contain Value Objects and Enums directly
- [ ] Controllers use Mappers for DTO → Response (explicit)
- [ ] Response schemas are simple (no magic)
- [ ] No queries in loops
- [ ] IDs are ValueObjects, not strings
- [ ] Entities have factory methods

---

**See also:**
- [Development Workflow](development-workflow.md) - **CONTRACT-FIRST process (READ THIS)**
- [Architecture](architecture.md) - DDD architecture overview
- [Application Layer](application-layer.md) - Queries and Commands
- [HTTP Layer](http-layer.md) - Controllers and Routers
- [Code Quality](code-quality.md) - SOLID principles and best practices
