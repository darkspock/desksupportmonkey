# Architecture

Complete guide to DDD (Domain-Driven Design) and Clean Architecture.

## Overview

This project follows **DDD** with **Clean Architecture** principles:

- **Framework-agnostic domain layer**
- Location: `/src` folder
- Follows Hexagonal Architecture
- Modern, clean Python code
- FastAPI as infrastructure framework

## Clean Architecture Structure

### Folder Structure:
```
src/
├── {bounded_context}_bc/
│   ├── {domain}/
│   │   ├── application/
│   │   │   ├── commands/         # Write operations (CQRS)
│   │   │   ├── queries/          # Read operations (CQRS)
│   │   │   ├── handlers/         # Event handlers
│   │   │   └── dtos/             # Data Transfer Objects
│   │   ├── domain/
│   │   │   ├── entities/         # Core business entities
│   │   │   ├── value_objects/    # Immutable values
│   │   │   ├── enums/            # Domain enumerations
│   │   │   ├── events/           # Domain events
│   │   │   ├── exceptions/       # Domain-specific exceptions
│   │   │   └── interfaces/       # Repository interfaces (ports)
│   │   └── infrastructure/
│   │       ├── models/           # SQLAlchemy ORM models
│   │       └── repositories/     # Repository implementations (adapters)

adapters/http/                    # HTTP Layer (Presentation)
├── {app}/                        # company_app, candidate_app, admin_app, public_app
│   └── {feature}/                # Feature folders (candidate, interview, job_position, etc.)
│       ├── controllers/          # HTTP controllers (may query multiple BCs)
│       ├── routers/              # FastAPI routers
│       ├── schemas/              # Request/Response Pydantic models
│       └── mappers/              # DTO to Response mappers
```

### Key Concepts:

#### Domain Layer
- **Business logic center**
- No external dependencies
- Pure business rules
- Framework-agnostic

#### Ports (Interfaces)
- Interfaces to outside world
- Defined in Domain layer
- Example: `CandidateRepositoryInterface`

#### Adapters (Implementations)
- Specific implementations of ports
- Located in Infrastructure layer
- Example: `CandidateRepository implements CandidateRepositoryInterface`

#### Application Layer (CQRS)
- Communicates domain with infrastructure
- Queries: Read operations (return DTOs)
- Commands: Write operations (return None)
- Handlers: Event handlers

#### Presentation Layer (HTTP Adapters)
- Located in `adapters/http/` (NOT in `src/{bc}/presentation/`)
- FastAPI controllers and routers
- Call Application layer (Queries/Commands)
- Transform DTOs to Response schemas using Mappers

---

## Bounded Contexts

### Current Bounded Contexts:

```
src/
├── auth_bc/                   # Authentication & Authorization
│   ├── organization/          # Multi-tenant organizations
│   ├── user/                  # User management
│   └── session/               # Session management
│
├── billing_bc/                # Subscriptions & Payments
│   ├── subscription/          # Plan management
│   └── payment/               # Payment processing
│
├── compliance_bc/             # Regulatory Framework Content
│   ├── framework/             # EU AI Act, NIST, ISO, etc.
│   ├── domain_area/           # Compliance domains
│   └── requirement/           # Framework requirements
│
├── assessment_bc/             # Assessment Engine
│   ├── assessment/            # Assessment sessions
│   ├── question/              # Universal questions
│   └── response/              # User responses
│
├── reporting_bc/              # Reports & Analytics
│   ├── report/                # Compliance reports
│   └── analytics/             # Dashboards & metrics
│
├── remediation_bc/            # Gap Tracking & Tasks
│   ├── gap/                   # Compliance gaps
│   └── task/                  # Remediation tasks
│
├── shared_bc/                 # Shared/cross-cutting
│   └── notification/          # Email notifications
│
└── framework/                 # Framework utilities
    ├── application/           # Base command/query classes
    ├── domain/                # Base entity, value objects
    └── infrastructure/        # Base repository, services
```

### Communication Between Bounded Contexts

#### Primary Method: Query and Command Bus
```python
# From one BC, get data from another BC
user = self.query_bus.query(GetUserByIdQuery(user_id))

# Trigger action in another BC
self.command_bus.execute(SendNotificationCommand(notification_data))
```

### What Can Leave a BC

#### ❌ Cannot Leave (Stay within BC):
- **Repositories** - Data access must stay internal
- **Entities** - Business entities are BC-specific
- **Domain Services** - Business logic stays internal

#### ✅ Can Leave (Can be shared):
- **Simple ValueObjects** - Example: `UserId`, `OrganizationId`, `AssessmentId`
- **Enums** - Example: `UserStatus`, `AssessmentStatus`

**Reasoning:** Simple, stable objects can be shared. Complex, evolving ones cannot.

---

## HTTP Layer - Controllers (CRITICAL)

### Controllers Are Thin Orchestrators

**Controllers should have MAX 3 responsibilities:**
1. **Parse request** - Extract data from request
2. **Dispatch Command/Query** - Delegate to Application layer
3. **Return response** - Convert DTO to Response via Mapper

### ❌ PROHIBITED in Controllers

**NEVER do these in Controllers:**

#### 1. NO Direct Database Access
```python
# ❌ WRONG
def get_user(self, user_id: str):
    result = self.session.execute(text("SELECT * FROM users"))
```

#### 2. NO Business Logic
```python
# ❌ WRONG - Validation logic
if not email and not phone:
    raise ValidationException()

# ❌ WRONG - Loops and processing
for assessment in assessments:
    # processing...

# ❌ WRONG - Calculations
score = correct_answers / total_questions * 100
```

#### 3. NO Direct Repository Access
```python
# ❌ WRONG
def get_user(self, user_id: str):
    return self.repository.get_by_id(user_id)
```

### ✅ CORRECT Controller Pattern

```python
class UserController:
    def __init__(
        self,
        command_bus: CommandBus,
        query_bus: QueryBus
    ):
        self.command_bus = command_bus
        self.query_bus = query_bus

    def get_user(self, user_id: str) -> UserResponse:
        # 1. Query
        dto = self.query_bus.query(
            GetUserByIdQuery(user_id=user_id)
        )

        # 2. Return via Mapper
        return UserMapper.dto_to_response(dto)

    def create_user(self, request: CreateUserRequest) -> UserResponse:
        # 1. Generate ID
        user_id = UserId.generate()

        # 2. Dispatch command (no return value)
        self.command_bus.execute(
            CreateUserCommand(
                user_id=user_id,
                email=request.email,
                first_name=request.first_name,
                last_name=request.last_name
            )
        )

        # 3. Query to get created entity
        dto = self.query_bus.query(
            GetUserByIdQuery(user_id=user_id)
        )

        # 4. Return via Mapper
        return UserMapper.dto_to_response(dto)
```

### Where Does Logic Go?

| What | Where | Why |
|------|-------|-----|
| Validation (email required) | Handler or Entity | Business rule |
| Duplicate checking | Repository | Data access logic |
| Loop through items | Handler | Processing logic |
| Insert to database | Repository | Data access |
| Publish events | Handler | Application orchestration |

---

## Layered Dependencies

```
HTTP Layer (FastAPI Controllers/Routers)
    ↓ depends on
Application Layer (Queries, Commands, Handlers)
    ↓ depends on
Domain Layer (Entities, Value Objects, Business Rules)
    ↑ defines interfaces for
Infrastructure Layer (Repositories, External Services)
```

**Key Rule:** Domain layer has NO dependencies. Everything depends on it.

---

## Routers vs Controllers

### Routers
- Define HTTP routes and OpenAPI documentation
- Located in `adapters/http/{app}/{feature}/routers/`
- Minimal logic - just route to controllers
- Handle request parsing and response formatting

### Controllers
- Business orchestration
- Located in `adapters/http/{app}/{feature}/controllers/`
- Call Command/Query bus (can query multiple BCs)
- Use Mappers for response conversion

### Example Structure:

```python
# adapters/http/api/auth/routers/user_router.py
router = APIRouter(prefix="/api/v1/users", tags=["users"])

@router.get("/{user_id}", response_model=UserResponse)
@inject
def get_user(
    user_id: str,
    controller: UserController = Depends(Provide[Container.user_controller])
) -> UserResponse:
    return controller.get_user(user_id)
```

```python
# adapters/http/api/auth/controllers/user_controller.py
class UserController:
    def __init__(self, query_bus: QueryBus, command_bus: CommandBus):
        self.query_bus = query_bus
        self.command_bus = command_bus

    def get_user(self, user_id: str) -> UserResponse:
        # Controller can query multiple BCs via bus
        user = self.query_bus.query(GetUserByIdQuery(user_id))
        organization = self.query_bus.query(GetOrganizationByIdQuery(user.organization_id))
        return UserMapper.dto_to_response(user, organization)
```

---

## Development Environment

- **Python 3.11+**
- **Docker** - All code runs in Docker
- **PostgreSQL** - Primary database
- **FastAPI** - Modern async framework
- **SQLAlchemy** - ORM with async support

---

## Architecture Decision Guidelines

### When to Use Full DDD:
- New domain with complex business rules
- Long-term maintainability critical
- Clear bounded context boundaries

### Before Creating New Domain:
1. Identify domain boundaries
2. Define entities, value objects
3. Design commands and queries
4. Identify domain events
5. **Only then start coding**

---

**See also:**
- [Critical Rules](critical-rules.md) - Performance and CQRS rules
- [Application Layer](application-layer.md) - CQRS implementation
- [Infrastructure](infrastructure.md) - Repositories and entities
- [Code Quality](code-quality.md) - SOLID principles
