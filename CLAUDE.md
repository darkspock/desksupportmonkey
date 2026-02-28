# DeskSupportMonkey

IT Service Desk & Asset Inventory Platform. Python 3.13 / FastAPI / SQLAlchemy / Celery / Redis. React 19 / TypeScript / Vite / Tailwind. Package managers: uv (backend), npm (frontend).

## Architecture

DDD + CQRS + Clean Architecture. Read `ai_docs/architecture/` before writing code — especially `critical-rules.md`.

**Framework base classes (mandatory):**
```python
from src.framework.application.command_bus import Command, CommandHandler
from src.framework.application.query_bus import Query, QueryHandler

@dataclass
class MyCommand(Command): ...
class MyHandler(CommandHandler[MyCommand]):
    def handle(self, cmd) -> None: ...

@dataclass
class MyQuery(Query): ...
class MyHandler(QueryHandler[MyQuery, ReturnType]):
    def handle(self, query) -> ReturnType: ...
```

**SQLAlchemy 2.0 style (mandatory):** `name: Mapped[str] = mapped_column(String(100))` — never bare `Column()`.

## AI Workflow

Full process: `ai_docs/development_process.md` (single source of truth for work types, phases, and output locations).

**Slash commands** (single-session):
- Requirements: `/requirement-write`, `/requirement-validate`, `/requirement-slice`, `/requirement-design`, `/requirement-tasks`
- Validation: `/check-dod`, `/check-architecture`, `/check-quality`, `/check-performance`, `/linter`, `/testing`

**Multi-session roles** (`ai/`): Master → Planner → Workers. See `ai/README.md`.

Agent instruction files: `ai_docs/agents/`. Philosophy: `ai_docs/working_documentation.md`.

## Progress Tracking (mandatory)

After implementation, always update:
1. **`docs/epics/{epic}/features/{feature}/tasks.md`** — mark checkboxes `- [x]`
2. **`docs/epics/{epic}/slicing.md`** — mark feature as "Done" in summary table
3. **`docs/product/roadmap.md`** — mark epic as "Done" when all features complete

## Commands

```bash
make test              # Unit tests (tests/unit/)
make test-integration  # Integration tests (requires Docker)
make test-all          # Both suites
make lint              # mypy + flake8
make start             # All services
make start-docker      # Infrastructure (PostgreSQL, Redis, Mailpit, MinIO)
make db-upgrade        # Apply migrations
make seed              # Demo data
```

## Testing (mandatory)

Standards in `ai_docs/architecture/testing.md`. Every feature/endpoint/bugfix needs tests:
- New endpoint → `tests/integration/test_{router}_endpoints.py`
- New command/query → `tests/unit/{bc}/`
- Bug fix → regression test

Both suites must pass. Fixtures in `tests/conftest.py`.

## Key Paths

- Source: `src/{bc}_bc/{subdomain}/` | Adapters: `adapters/http/api/` | Frontend: `web/app/src/`
- Tests: `tests/unit/`, `tests/integration/` | Migrations: `alembic/versions/` | Docs: `docs/epics/`
