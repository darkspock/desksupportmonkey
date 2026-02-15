# Infrastructure Layer

Complete guide to Repositories, Entities, Models, and Mappers.

## Overview

The Infrastructure Layer contains:
- **Repository Implementations** - Data access adapters
- **SQLAlchemy Models** - Database ORM models
- **External Service Adapters** - Email, storage, etc.

---

## Repository Pattern

### Repository Interface (Port)

Located in: `domain/interfaces/`

```python
from abc import ABC, abstractmethod
from typing import Optional, List

class CandidateRepositoryInterface(ABC):
    """Repository interface for Candidate entity"""

    @abstractmethod
    def get_by_id(self, candidate_id: CandidateId) -> Optional[Candidate]:
        """Get candidate by ID"""
        pass

    @abstractmethod
    def find_by_email(self, email: str) -> Optional[Candidate]:
        """Find candidate by email"""
        pass

    @abstractmethod
    def find_by_company(self, company_id: CompanyId) -> List[Candidate]:
        """Find all candidates for a company"""
        pass

    @abstractmethod
    def save(self, candidate: Candidate) -> None:
        """Save candidate"""
        pass

    @abstractmethod
    def delete(self, candidate_id: CandidateId) -> None:
        """Delete candidate"""
        pass
```

### Repository Implementation (Adapter)

Located in: `infrastructure/repositories/`

```python
from sqlalchemy.orm import Session
from typing import Optional, List

class CandidateRepository(CandidateRepositoryInterface):
    """SQLAlchemy implementation of CandidateRepository"""

    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, candidate_id: CandidateId) -> Optional[Candidate]:
        model = self.session.query(CandidateModel).filter(
            CandidateModel.id == str(candidate_id)
        ).first()

        if not model:
            return None

        return self._to_entity(model)

    def find_by_email(self, email: str) -> Optional[Candidate]:
        model = self.session.query(CandidateModel).filter(
            CandidateModel.email == email
        ).first()

        if not model:
            return None

        return self._to_entity(model)

    def find_by_company(self, company_id: CompanyId) -> List[Candidate]:
        models = self.session.query(CandidateModel).filter(
            CandidateModel.company_id == str(company_id)
        ).all()

        return [self._to_entity(m) for m in models]

    def save(self, candidate: Candidate) -> None:
        model = self._to_model(candidate)

        existing = self.session.query(CandidateModel).filter(
            CandidateModel.id == str(candidate.id)
        ).first()

        if existing:
            # Update existing
            for key, value in model.__dict__.items():
                if not key.startswith('_'):
                    setattr(existing, key, value)
        else:
            # Insert new
            self.session.add(model)

        self.session.commit()

    def delete(self, candidate_id: CandidateId) -> None:
        self.session.query(CandidateModel).filter(
            CandidateModel.id == str(candidate_id)
        ).delete()
        self.session.commit()

    # --- Private Methods ---

    def _to_entity(self, model: CandidateModel) -> Candidate:
        """Convert SQLAlchemy model to domain entity"""
        return Candidate(
            id=CandidateId(model.id),
            name=model.name,
            email=model.email,
            status=CandidateStatus(model.status),
            created_at=model.created_at,
            updated_at=model.updated_at
        )

    def _to_model(self, entity: Candidate) -> CandidateModel:
        """Convert domain entity to SQLAlchemy model"""
        return CandidateModel(
            id=str(entity.id),
            name=entity.name,
            email=entity.email,
            status=entity.status.value,
            created_at=entity.created_at,
            updated_at=entity.updated_at
        )
```

### Repository Rules

1. **Repositories are stateless** - Only `session` as dependency
2. **Public methods return ONLY:**
   - Entities
   - Collections of entities
   - Optional entities
   - Scalar values (`int`, `str`, `bool`)
3. **Never return SQLAlchemy models directly**
4. **Always convert to domain entities**

---

## SQLAlchemy Models

### Model Location

Located in: `infrastructure/models/`

### Model Structure

```python
from sqlalchemy import Column, String, DateTime, Enum
from sqlalchemy.orm import relationship
from core.database import Base
from datetime import datetime

class CandidateModel(Base):
    """SQLAlchemy model for candidates table"""

    __tablename__ = "candidates"

    id = Column(String(26), primary_key=True)  # ULID
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, unique=True)
    status = Column(String(50), nullable=False, default="PENDING")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=True, onupdate=datetime.utcnow)

    # Relationships
    interviews = relationship("InterviewModel", back_populates="candidate")
    comments = relationship("CommentModel", back_populates="candidate")
```

### Model Rules

1. **Models are in infrastructure layer** - Separate from entities
2. **Use string IDs** - ULIDs stored as strings
3. **Define relationships** - For eager loading
4. **Use SQLAlchemy types** - Column, String, DateTime, etc.

---

## Domain Entities

### Entity Location

Located in: `domain/entities/`

### Entity Structure

```python
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List

@dataclass
class Candidate:
    """Candidate domain entity"""

    _id: CandidateId
    _name: str
    _email: str
    _status: CandidateStatus
    _created_at: datetime
    _updated_at: Optional[datetime] = None
    _domain_events: List[DomainEvent] = field(default_factory=list)

    # --- Properties (Read-only access) ---

    @property
    def id(self) -> CandidateId:
        return self._id

    @property
    def name(self) -> str:
        return self._name

    @property
    def email(self) -> str:
        return self._email

    @property
    def status(self) -> CandidateStatus:
        return self._status

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def updated_at(self) -> Optional[datetime]:
        return self._updated_at

    # --- Factory Methods ---

    @classmethod
    def create(cls, name: str, email: str) -> "Candidate":
        """Factory method for creating new candidates"""
        # Validation
        if not email or "@" not in email:
            raise InvalidEmailError(email)
        if not name or len(name) < 2:
            raise InvalidNameError(name)

        candidate = cls(
            _id=CandidateId.generate(),
            _name=name,
            _email=email,
            _status=CandidateStatus.PENDING,
            _created_at=datetime.utcnow()
        )

        # Record domain event
        candidate._record_event(
            CandidateCreatedEvent(
                candidate_id=str(candidate.id),
                name=name,
                email=email
            )
        )

        return candidate

    # --- Update Methods ---

    def update_details(self, name: str, email: str) -> None:
        """Update candidate details"""
        if not email or "@" not in email:
            raise InvalidEmailError(email)

        old_email = self._email
        self._name = name
        self._email = email
        self._updated_at = datetime.utcnow()

        if old_email != email:
            self._record_event(
                CandidateEmailUpdatedEvent(
                    candidate_id=str(self.id),
                    old_email=old_email,
                    new_email=email
                )
            )

    def activate(self) -> None:
        """Activate candidate"""
        if self._status == CandidateStatus.ACTIVE:
            raise CandidateAlreadyActiveError(str(self.id))

        self._status = CandidateStatus.ACTIVE
        self._updated_at = datetime.utcnow()

        self._record_event(
            CandidateActivatedEvent(candidate_id=str(self.id))
        )

    def archive(self) -> None:
        """Archive candidate"""
        self._status = CandidateStatus.ARCHIVED
        self._updated_at = datetime.utcnow()

    # --- Domain Events ---

    def _record_event(self, event: DomainEvent) -> None:
        """Record a domain event"""
        self._domain_events.append(event)

    def pull_domain_events(self) -> List[DomainEvent]:
        """Pull and clear domain events"""
        events = self._domain_events.copy()
        self._domain_events.clear()
        return events
```

### Entity Rules

1. **Constructor is for repository hydration only**
   - Use underscore prefix for properties (`_id`, `_name`)
   - No validation in constructor

2. **Factory methods for creation**
   - `create()` class method for new entities
   - Contains validation and business logic
   - Records domain events

3. **Update methods for modifications**
   - Named methods like `update_details()`, `activate()`
   - Contains validation
   - Records domain events

4. **Status changes through specific methods**
   - Don't allow direct status assignment
   - Use `activate()`, `archive()`, etc.

5. **Properties for read access**
   - Use `@property` decorator
   - Return copies for collections

---

## Value Objects

### Value Object Location

Located in: `domain/value_objects/` or `framework/domain/value_objects/`

### ID Value Objects

```python
from src.framework.domain.value_objects import Ulid

class CandidateId(Ulid):
    """Value object for Candidate ID"""
    pass

class CompanyId(Ulid):
    """Value object for Company ID"""
    pass
```

### Complex Value Objects

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class Email:
    """Value object for email address"""
    value: str

    def __post_init__(self):
        if not self.value or "@" not in self.value:
            raise InvalidEmailError(self.value)

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class Money:
    """Value object for monetary amounts"""
    amount: int  # In cents
    currency: str = "USD"

    def add(self, other: "Money") -> "Money":
        if self.currency != other.currency:
            raise CurrencyMismatchError()
        return Money(self.amount + other.amount, self.currency)

    def to_display(self) -> str:
        return f"{self.currency} {self.amount / 100:.2f}"
```

### Value Object Rules

1. **Immutable** - Use `frozen=True` in dataclass
2. **Validated on creation** - Use `__post_init__`
3. **Equality by value** - Two VOs with same values are equal
4. **No identity** - No ID, identified by their values

---

## Mappers

This codebase uses **two types of Mappers**:
1. **DtoMapper** (Application layer) - Entity → DTO
2. **ResponseMapper** (Presentation layer) - DTO → Response

### Conversion Flow

```
Entity → DtoMapper → DTO (with Value Objects) → ResponseMapper → Response (primitives)
```

---

### DtoMapper (Entity → DTO)

**Location:** `application/queries/shared/`

```python
class CandidateDtoMapper:
    """Mapper for Entity to DTO conversion"""

    @staticmethod
    def from_model(candidate: Candidate) -> CandidateDto:
        return CandidateDto(
            id=candidate.id,           # Keep as ValueObject
            name=candidate.name,
            email=candidate.email,
            status=candidate.status,   # Keep as Enum
            created_at=candidate.created_at,
            updated_at=candidate.updated_at
        )
```

**Rules:**
- Located in **application layer**
- Keep Value Objects and Enums (don't serialize)
- Used in QueryHandlers

---

### ResponseMapper (DTO → Response)

**Location:** `presentation/mappers/`

```python
class CandidateMapper:
    """Mapper for DTO to Response conversion - EXPLICIT"""

    @staticmethod
    def dto_to_response(dto: CandidateDto) -> CandidateResponse:
        return CandidateResponse(
            id=str(dto.id.value),              # ValueObject → string
            name=dto.name,
            status=dto.status.value,           # Enum → string
            created_at=dto.created_at.isoformat()  # datetime → ISO string
        )
```

**Rules:**
- Located in **presentation layer**
- Converts Value Objects to primitives (explicit)
- Converts Enums to strings (explicit)
- Used in Controllers

---

## Migrations (Alembic)

### Creating Migrations

```bash
make revision m="add_candidates_table"
```

### Migration Structure

```python
# alembic/versions/xxxx_add_candidates_table.py
from alembic import op
import sqlalchemy as sa

revision = 'xxxx'
down_revision = 'yyyy'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        'candidates',
        sa.Column('id', sa.String(26), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('status', sa.String(50), nullable=False, default='PENDING'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True)
    )

def downgrade() -> None:
    op.drop_table('candidates')
```

### Running Migrations

```bash
make migrate
```

---

## Entity vs Model: Key Differences

| Aspect | Entity (Domain) | Model (Infrastructure) |
|--------|-----------------|------------------------|
| Location | `domain/entities/` | `infrastructure/models/` |
| Purpose | Business logic | Database mapping |
| Dependencies | None | SQLAlchemy |
| Validation | In factory methods | None |
| Events | Records domain events | None |
| ID Type | ValueObject (`CandidateId`) | String |

---

**See also:**
- [Application Layer](application-layer.md) - Queries and Commands using repositories
- [Code Quality](code-quality.md) - SOLID principles for entities
- [Architecture](architecture.md) - DDD structure
- [Critical Rules](critical-rules.md) - Performance and best practices
