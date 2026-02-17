# Contributing to Desk Support Monkey

Thank you for your interest in contributing! This project is built entirely with AI using spec-driven development, and we welcome contributions that follow our quality standards.

## Getting Started

1. Fork the repository
2. Clone your fork
3. Set up the development environment:

```bash
# Backend
uv sync
make start-docker    # PostgreSQL, Redis, MinIO
make db-upgrade      # Apply migrations
make seed            # Load demo data

# Frontend
cd web/app && npm install
```

## Development Rules

### All code must pass tests and type checking

This is non-negotiable. Every pull request must:

- **Pass all existing tests** — `make test`
- **Pass mypy type checking** — `make lint`
- **Include tests for new code** — No untested code will be merged
- **Pass flake8 linting** — `make lint`

```bash
# Run before submitting
make test    # PYTHONPATH=src uv run pytest tests/ -v
make lint    # mypy + flake8
```

### Architecture

This project follows **DDD + CQRS + Clean Architecture**. Before writing code, read:

- `ai_docs/architecture/critical-rules.md` — The 6 non-negotiable rules
- `ai_docs/architecture/architecture.md` — Bounded context structure
- `ai_docs/architecture/application-layer.md` — Command/query patterns
- `ai_docs/architecture/infrastructure.md` — Repository conventions
- `ai_docs/architecture/http-layer.md` — Router and schema standards

Key principles:

- **Bounded contexts are isolated** — No cross-context imports at the domain level
- **CQRS** — Separate command handlers (writes) from query handlers (reads)
- **Hexagonal architecture** — Domain has no infrastructure dependencies
- **Repositories** — All database access goes through repository interfaces

### Backend conventions

- Python 3.13, FastAPI, SQLAlchemy, Alembic
- Package manager: **uv** (not pip)
- Tests in `tests/unit/` organized by bounded context
- One command/query handler per file
- Pydantic schemas for API request/response validation
- ULID for all entity IDs

### Frontend conventions

- React 19, TypeScript (strict mode), Vite, Tailwind CSS
- Package manager: **npm**
- TanStack React Query for server state
- i18n support required (English and Spanish)
- TypeScript must compile with no errors: `cd web/app && npx tsc -b`

## Pull Request Process

1. Create a feature branch from `main`
2. Make your changes following the architecture rules
3. Write or update tests
4. Run `make test && make lint` — both must pass
5. Run `cd web/app && npx tsc -b` if you touched frontend code
6. Open a PR with a clear description of what and why

## What to Contribute

Check the [roadmap](docs/product/roadmap.md) for pending epics (E11-E34). If you want to tackle one:

1. Open an issue first to discuss the approach
2. Follow the spec-driven workflow: requirements → design → tasks → implement → validate

Bug fixes, test improvements, and documentation improvements are always welcome.

## Code of Conduct

Be respectful. Write clean code. Test your work. That's it.
