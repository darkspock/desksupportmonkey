# DeskSupportMonkey - Claude Code Instructions

## Project Overview

IT Service Desk & Asset Inventory Platform built with DDD + CQRS + Clean Architecture.
- **Backend:** Python 3.13, FastAPI, SQLAlchemy, Alembic, Celery, Redis
- **Frontend:** React 19, TypeScript, Vite, Tailwind CSS, TanStack React Query
- **Package Manager:** uv (backend), npm (frontend)

## Architecture Rules

Before writing any code, read and follow:
- `ai_docs/architecture/critical-rules.md` — The 6 non-negotiable architecture rules
- `ai_docs/architecture/architecture.md` — DDD bounded context structure
- `ai_docs/architecture/application-layer.md` — CQRS command/query patterns
- `ai_docs/architecture/infrastructure.md` — Repository and ORM conventions
- `ai_docs/architecture/http-layer.md` — Router and schema standards
- `ai_docs/architecture/code-quality.md` — Naming and style guidelines
- `ai_docs/architecture/testing.md` — Testing standards (unit + integration)
- `ai_docs/architecture/frontend/` — Frontend architecture and coding standards

### MANDATORY: Framework Base Classes (NEVER skip this)

ALL commands and queries MUST inherit from base classes in `src/framework/`:

- `from src.framework.application.command_bus import Command, CommandHandler`
- `from src.framework.application.query_bus import Query, QueryHandler`

Pattern:
- `@dataclass class MyCommand(Command):`
- `class MyHandler(CommandHandler[MyCommand]):`  with `def handle(...) -> None`
- `@dataclass class MyQuery(Query):`
- `class MyHandler(QueryHandler[MyQuery, ReturnType]):`

NEVER create standalone command/query classes without this inheritance.

### SQLAlchemy: Use `Mapped` for column type annotations

All SQLAlchemy model column definitions MUST use `Mapped[type]` annotations (SQLAlchemy 2.0 style) instead of bare `Column()`. This ensures mypy correctly infers attribute types and avoids type errors.

Example: `name: Mapped[str] = mapped_column(String(100))` instead of `name = Column(String(100))`.

## AI Development Pipeline

The project uses 10 AI agents defined in `ai_docs/agents/`. These are invocable via slash commands:

### Requirements Phase
- `/requirement-write` — Create structured requirement documents
- `/requirement-validate` — Validate completeness
- `/requirement-slice` — Break epics into features
- `/requirement-design` — Produce technical design
- `/requirement-tasks` — Convert design into tasks

### Validation Phase (post-implementation)
- `/check-dod` — Verify acceptance criteria met
- `/check-architecture` — Validate DDD/CQRS compliance
- `/check-quality` — Review SOLID principles
- `/check-performance` — Detect N+1, missing indexes
- `/linter` — Run mypy + flake8
- `/testing` — Analyze coverage and test quality

## Working Documentation

Read `ai_docs/working_documentation.md` for documentation types and workflows.

## Progress Tracking (MANDATORY)

After completing implementation work, ALWAYS update progress tracking documents:

### 1. Task Documents (`tasks.md`)
- Each feature has a `tasks.md` file under `docs/epics/{epic}/features/{feature}/tasks.md`
- Tasks have checkboxes: `- [ ]` (pending) → `- [x]` (done)
- Mark individual acceptance criteria/tasks as done when completed

### 2. Slicing Documents (`slicing.md`)
- Each epic has a `slicing.md` file under `docs/epics/{epic}/slicing.md`
- Contains a "Features Summary" table
- When ALL tasks of a feature are complete, add a "Status" column if not present and mark the feature as "Done"

### 3. Roadmap (`docs/product/roadmap.md`)
- Contains an "Epic Overview" table with a Status column
- When ALL features of an epic are complete, change Status from "Pending" to "Done"

**NEVER skip progress tracking. Update these documents as part of completing any implementation work.**

## Common Commands

```bash
make test              # Run unit tests (tests/unit/)
make test-integration  # Run integration tests (tests/integration/, requires Docker)
make test-all          # Run all tests (unit + integration)
make lint              # Run mypy + flake8
make start             # Start all services
make start-docker      # Start infrastructure (PostgreSQL, Redis, Mailpit, MinIO)
make db-upgrade        # Apply migrations
make seed              # Load demo data
```

## Testing (MANDATORY)

Read `ai_docs/architecture/testing.md` for full testing standards.

**Every new feature, endpoint, or bug fix MUST include tests:**

- **New endpoint** → Add integration test in `tests/integration/test_{router}_endpoints.py`
- **New command/query handler** → Add unit test in `tests/unit/{bc}/`
- **Bug fix** → Add a regression test that reproduces the bug

**Both test suites MUST pass before work is considered complete:**
- Unit tests (`tests/unit/`) — Fast, isolated, use `MagicMock`
- Integration tests (`tests/integration/`) — Real PostgreSQL, full HTTP stack

Shared test fixtures (DB session, TestClient, auth helpers) are in `tests/conftest.py`.

## Key Paths

- Backend source: `src/{bounded_context}_bc/{subdomain}/`
- HTTP adapters: `adapters/http/api/`
- Frontend: `web/app/src/`
- Unit tests: `tests/unit/`
- Integration tests: `tests/integration/`
- Test fixtures: `tests/conftest.py`
- Migrations: `alembic/versions/`
- Epic docs: `docs/epics/`
- Roadmap: `docs/product/roadmap.md`
