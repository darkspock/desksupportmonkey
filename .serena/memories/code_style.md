# Code Style & Conventions

## Python
- Python 3.13
- Type hints used throughout
- @dataclass for Commands, Queries, and DTOs
- Domain entities: plain classes with factory methods
- mypy for type checking (ignore_missing_imports=true)
- flake8 for linting
- autopep8 for formatting
- No docstrings required unless logic is non-obvious

## Naming
- Bounded contexts: `{name}_bc` (e.g., `incident_bc`)
- Commands: `CreateIncidentCommand`, handler: `CreateIncidentCommandHandler`
- Queries: `ListIncidentsQuery`, handler: `ListIncidentsQueryHandler`
- DTOs: `IncidentDto` with `from_entity()` factory
- Mappers: `IncidentMapper` with `dto_to_response()` static method
- Value Objects for IDs: `IncidentId(Ulid)`
- Enums: `IncidentStatusEnum`

## Frontend (TypeScript/React)
- React 19 + TypeScript
- Vite build tool
- Tailwind CSS for styling
- Pages organized by role: auth/, admin/, employee/, technician/, superadmin/
- Shared components in web/app/src/components/
- i18n in web/app/src/locales/

## Testing
- pytest with asyncio_mode=auto
- Unit tests: tests/unit/{bc}/
- Integration tests: tests/integration/ (requires Docker PostgreSQL)
- E2E tests: tests/e2e/
- Fixtures in tests/conftest.py
- factory-boy + faker for test data
