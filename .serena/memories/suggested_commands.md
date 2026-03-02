# Suggested Commands

## Starting Services
```bash
make start              # All services (Docker + Backend + Celery + Frontend)
make stop               # Stop all services
make start-docker       # Only Docker (PostgreSQL:5443, Redis:6398, Mailpit:8028, MinIO:9001)
make start-backend      # Only FastAPI (port 8001)
make start-frontend     # Only Vite dev server (port 5173)
make queue              # Celery worker (reports queue)
```

## Database
```bash
make db-upgrade                  # Apply migrations
make db-migrate msg="description" # Create new migration
make db-downgrade                # Rollback one migration
make seed                        # Seed demo data
make demo-reset                  # Reset DB + seed
```

## Testing
```bash
make test               # Unit tests (tests/unit/)
make test-integration   # Integration tests (requires Docker)
make test-all           # All tests
```

## Code Quality
```bash
make lint               # mypy + flake8
make scan               # OWASP ZAP API scan
make clean              # Remove __pycache__, .pytest_cache, .mypy_cache
```

## Dependencies
```bash
make install            # Backend (uv sync) + Frontend (npm install)
uv sync --all-extras    # Backend only
cd web/app && npm install # Frontend only
```

## White Label / Multi-Brand
```bash
make build-brand BRAND=dsm        # Build frontend for brand
make start-brand BRAND=dsm        # Start backend with brand env
make db-upgrade-brand BRAND=dsm   # Apply migrations for brand
```

## Stripe (local testing)
```bash
make stripe-login       # Authenticate Stripe CLI
make stripe-listen      # Forward webhooks to localhost:8001
```

## System Utilities (macOS/Darwin)
```bash
git status / git diff / git log   # Version control
ls / find / grep                   # File system (Darwin versions)
```

## Service URLs (local)
- Frontend: http://localhost:5173
- Backend API: http://localhost:8001
- API Docs (Swagger): http://localhost:8001/docs
- Mailpit: http://localhost:8028
- MinIO Console: http://localhost:9001
