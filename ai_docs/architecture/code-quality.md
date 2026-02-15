# Code Quality & Best Practices

SOLID principles, naming conventions, enums, and domain layer best practices.

## SOLID Principles

### Single Responsibility Principle (SRP)

**Rule:** A class should solve ONE problem (not do one thing)

#### Understanding SRP

❌ **Common Misunderstanding:**
"A class should only have one method"

✅ **Correct Understanding:**
"A class should focus on solving one problem"

#### Example:

```python
# ✅ CORRECT - One responsibility: Candidate repository
class CandidateRepository:
    def get_by_id(self, candidate_id: CandidateId) -> Optional[Candidate]: ...
    def find_by_email(self, email: str) -> Optional[Candidate]: ...
    def find_by_company(self, company_id: CompanyId) -> List[Candidate]: ...
    def save(self, candidate: Candidate) -> None: ...
    # Multiple methods, but ONE responsibility: Candidate data access
```

#### Large Files with Single Responsibility

**Problem:** File is huge but has single responsibility

**Solution:** Split into sub-responsibilities

```python
# Before: candidate_repository.py (2000 lines)
class CandidateRepository:
    def get_by_id(self) -> Candidate: ...
    def find_by_email(self) -> Candidate: ...
    def find_with_stats(self) -> CandidateStatsDto: ...
    def find_with_interviews(self) -> CandidateWithInterviewsDto: ...
    # ... 50 more methods

# After: Split by sub-responsibility
# candidate_repository.py (core methods)
class CandidateRepository:
    def get_by_id(self) -> Candidate: ...
    def save(self) -> None: ...

# candidate_query_repository.py (complex queries)
class CandidateQueryRepository:
    def find_with_stats(self) -> CandidateStatsDto: ...
    def find_with_interviews(self) -> CandidateWithInterviewsDto: ...
```

### Dependency Principle - "Ask Only What You Need"

**Rule:** A method should only ask for what it actually needs.

#### Bad Example:
```python
def send_welcome_email(self, candidate: Candidate) -> None:
    email = candidate.email
    self.mailer.send(email, "Welcome!")
    # Only needs email, but coupled to entire Candidate object

# Problems:
# - Can't reuse for non-Candidate emails
# - Hard to test (need full Candidate)
# - Breaks when Candidate changes
```

#### Good Example:
```python
def send_welcome_email(self, email: str, name: str) -> None:
    self.mailer.send(email, f"Welcome {name}!")
    # Only asks for what it needs

# Benefits:
# - Reusable for any email
# - Easy to test (just pass strings)
# - Not affected by Candidate changes
```

### Stateless Business Services

**Rule:** Services should NEVER store state

#### Correct Pattern:
```python
class InterviewScheduler:
    def __init__(self, calendar_service: CalendarServiceInterface):
        self.calendar_service = calendar_service  # Dependency, not state

    def schedule(self, interview: Interview, datetime: datetime) -> None:
        # No state stored, just computation
        self.calendar_service.create_event(interview, datetime)
```

#### Wrong Pattern - Services with State:
```python
class InterviewScheduler:
    def __init__(self):
        self.scheduled_interviews = []  # ❌ STATE!

    def add_interview(self, interview: Interview) -> None:
        self.scheduled_interviews.append(interview)

    def get_scheduled(self) -> List[Interview]:
        return self.scheduled_interviews

# Problems:
# - Shared state between calls
# - Not thread-safe
# - Hard to test
```

---

## Domain Layer Best Practices

### Business Logic in Entities ✅

**Should be in entity:**
- Validate data and maintain invariants
- Business relationships within the domain
- Calculations and business rules specific to entity

```python
class Candidate:
    def change_email(self, new_email: str) -> None:
        # Invariant: Email must be valid
        if not new_email or "@" not in new_email:
            raise InvalidEmailError(new_email)

        old_email = self._email
        self._email = new_email
        self._record_event(
            CandidateEmailChangedEvent(str(self.id), old_email, new_email)
        )

    @property
    def full_name(self) -> str:
        # Calculation within entity
        return f"{self._first_name} {self._last_name}"

    def is_active(self) -> bool:
        # Business rule specific to candidate
        return self._status == CandidateStatus.ACTIVE
```

### Business Logic in Domain Services ✅

**Should be in domain service:**
- Rules involving external entities
- Rules between different instances of entities
- Complex validations requiring repository access

```python
class InterviewSchedulingService:
    def __init__(self, interview_repository: InterviewRepositoryInterface):
        self.interview_repository = interview_repository

    def can_schedule_interview(
        self,
        candidate_id: CandidateId,
        datetime: datetime
    ) -> bool:
        # Needs repository - can't be in entity
        existing = self.interview_repository.find_by_candidate_and_datetime(
            candidate_id,
            datetime
        )
        return existing is None
```

---

## Naming Conventions

### Query/Command Naming

#### Verbs:

| Verb | Usage | Returns |
|------|-------|---------|
| `Get` | Expects to find, raises if not | Entity/DTO |
| `Find` | May or may not find | Optional/List |
| `List` | Returns collection | List |
| `Search` | Complex filtered search | List |
| `Create` | Creates new entity | None |
| `Update` | Updates existing entity | None |
| `Delete` | Removes entity | None |

#### Examples:
```python
GetCandidateByIdQuery        # Raises if not found
FindCandidateByEmailQuery    # Returns Optional[CandidateDto]
ListCandidatesQuery          # Returns List[CandidateDto]
SearchCandidatesQuery        # With filters, pagination

CreateCandidateCommand       # Creates candidate
UpdateCandidateCommand       # Updates candidate
DeleteCandidateCommand       # Deletes candidate
ArchiveCandidateCommand      # Archives candidate
```

### File Naming

| Type | Naming | Example |
|------|--------|---------|
| Entity | `{name}.py` | `candidate.py` |
| Repository Interface | `{name}_repository_interface.py` | `candidate_repository_interface.py` |
| Repository | `{name}_repository.py` | `candidate_repository.py` |
| Model | `{name}.py` (in models/) | `candidate.py` |
| Query | `{verb}_{name}_query.py` | `get_candidate_by_id_query.py` |
| Command | `{verb}_{name}_command.py` | `create_candidate_command.py` |
| DTO | `{name}_dto.py` | `candidate_dto.py` |
| Mapper | `{name}_mapper.py` | `candidate_mapper.py` |

### Variable Naming

```python
# ✅ CORRECT
candidate_id = CandidateId.generate()
interview_datetime = datetime.now()
is_active = True

# ❌ WRONG
id = CandidateId.generate()      # Too generic
dt = datetime.now()               # Abbreviation
active = True                     # Not clear it's a boolean
```

---

## Enums

### Enum Location

Located in: `domain/enums/`

### Enum Structure

```python
from enum import Enum

class CandidateStatus(str, Enum):
    """Status of a candidate in the system"""
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    REJECTED = "REJECTED"
    ARCHIVED = "ARCHIVED"

    @property
    def is_active(self) -> bool:
        """Check if status is active"""
        return self == CandidateStatus.ACTIVE

    @property
    def can_be_contacted(self) -> bool:
        """Check if candidate can be contacted"""
        return self in (CandidateStatus.PENDING, CandidateStatus.ACTIVE)
```

### Allowed Functionality in Enums

#### 1. Properties for Simple Checks
```python
class InterviewStatus(str, Enum):
    SCHEDULED = "SCHEDULED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

    @property
    def is_final(self) -> bool:
        return self in (self.COMPLETED, self.CANCELLED)
```

#### 2. Decoration (Labels)
```python
class CandidateStatus(str, Enum):
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"

    @property
    def label(self) -> str:
        labels = {
            self.PENDING: "Pending Review",
            self.ACTIVE: "Active Candidate"
        }
        return labels[self]
```

#### 3. Mappings Between Systems
```python
class ExternalStatus(str, Enum):
    APPROVED = "approved"
    REJECTED = "rejected"

    def to_internal_status(self) -> CandidateStatus:
        mapping = {
            self.APPROVED: CandidateStatus.ACTIVE,
            self.REJECTED: CandidateStatus.REJECTED
        }
        return mapping[self]
```

### When NOT to Add to Enum

❌ **Don't add if logic is complex:**

```python
# ❌ BAD - Too complex for enum
class CandidateStatus(str, Enum):
    ACTIVE = "ACTIVE"

    def calculate_score(
        self,
        interviews: List[Interview],
        reviews: List[Review]
    ) -> int:
        # Too complex - belongs in service
        pass

# ✅ GOOD - Move to service
class CandidateScoreCalculator:
    def calculate(
        self,
        candidate: Candidate,
        interviews: List[Interview]
    ) -> int:
        # Complex logic here
        pass
```

---

## Type Hints

### Always Use Type Hints

```python
from typing import Optional, List, Dict

def get_candidate(self, candidate_id: CandidateId) -> Optional[Candidate]:
    pass

def find_all(self) -> List[Candidate]:
    pass

def get_stats(self) -> Dict[str, int]:
    pass
```

### Complex Types

```python
from typing import TypeVar, Generic

T = TypeVar('T')

class Repository(Generic[T]):
    def get_by_id(self, id: str) -> Optional[T]:
        pass

class CandidateRepository(Repository[Candidate]):
    pass
```

---

## Error Handling

### Domain Exceptions

```python
# domain/exceptions/candidate_exceptions.py

class CandidateException(Exception):
    """Base exception for candidate domain"""
    pass

class CandidateNotFoundException(CandidateException):
    def __init__(self, candidate_id: str):
        self.candidate_id = candidate_id
        super().__init__(f"Candidate not found: {candidate_id}")

class InvalidEmailError(CandidateException):
    def __init__(self, email: str):
        self.email = email
        super().__init__(f"Invalid email: {email}")

class CandidateAlreadyExistsError(CandidateException):
    def __init__(self, email: str):
        self.email = email
        super().__init__(f"Candidate already exists with email: {email}")
```

### Exception Handling in Handlers

```python
class CreateCandidateCommandHandler(CommandHandler[CreateCandidateCommand]):
    def execute(self, command: CreateCandidateCommand) -> None:
        # Check for existing candidate
        existing = self.repository.find_by_email(command.email)
        if existing:
            raise CandidateAlreadyExistsError(command.email)

        # Create candidate (validation in entity factory)
        candidate = Candidate.create(
            name=command.name,
            email=command.email
        )

        self.repository.save(candidate)
```

---

## Testing

### Test Structure

```
tests/
├── unit/
│   ├── candidate/
│   │   ├── commands/
│   │   │   └── test_create_candidate_command.py
│   │   ├── queries/
│   │   │   └── test_get_candidate_by_id_query.py
│   │   └── domain/
│   │       └── test_candidate_entity.py
├── integration/
│   └── test_candidate_repository.py
└── conftest.py
```

### Unit Test Example

```python
import pytest
from src.candidate_bc.candidate.domain.entities.candidate import Candidate

class TestCandidateEntity:
    def test_create_candidate_with_valid_data(self):
        # Arrange & Act
        candidate = Candidate.create(
            name="John Doe",
            email="john@example.com"
        )

        # Assert
        assert candidate.name == "John Doe"
        assert candidate.email == "john@example.com"
        assert candidate.status == CandidateStatus.PENDING

    def test_create_candidate_with_invalid_email_raises_error(self):
        # Act & Assert
        with pytest.raises(InvalidEmailError):
            Candidate.create(
                name="John Doe",
                email="invalid-email"
            )
```

---

## Code Organization Checklist

Before committing code, verify:

- [ ] Classes follow Single Responsibility Principle
- [ ] Methods ask only for what they need
- [ ] Services are stateless
- [ ] Business logic is in entities or domain services
- [ ] Enums don't have complex logic
- [ ] Type hints are used everywhere
- [ ] Exceptions are domain-specific
- [ ] Naming follows conventions
- [ ] Tests cover the new code

---

**See also:**
- [Architecture](architecture.md) - DDD structure
- [Application Layer](application-layer.md) - Queries and Commands
- [Infrastructure](infrastructure.md) - Repositories and Entities
- [Critical Rules](critical-rules.md) - Performance and CQRS rules
