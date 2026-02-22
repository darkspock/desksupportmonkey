.PHONY: start stop start-docker start-backend start-frontend start-frontend-bg queue start-queue-bg install install-frontend logs db-migrate db-upgrade test test-integration test-all lint scan clean seed demo-reset

# Colors for terminal output
GREEN := \033[0;32m
YELLOW := \033[0;33m
NC := \033[0m # No Color

# =============================================================================
# Main Commands
# =============================================================================

## Start all services (Docker + Backend + Celery + Frontend)
start:
	@echo "$(GREEN)Starting all services...$(NC)"
	@make start-docker
	@echo "$(GREEN)Waiting for Docker services to be healthy...$(NC)"
	@sleep 3
	@make start-queue-bg
	@make start-frontend-bg
	@make start-backend

## Stop all services
stop:
	@echo "$(YELLOW)Stopping all services...$(NC)"
	@-pkill -f "uvicorn app:app" 2>/dev/null || true
	@-pkill -f "celery" 2>/dev/null || true
	@-pkill -f "vite.*web/app" 2>/dev/null || true
	@docker-compose down
	@echo "$(GREEN)All services stopped$(NC)"

# =============================================================================
# Individual Services
# =============================================================================

## Start Docker containers (PostgreSQL, Redis, Mailpit, MinIO)
start-docker:
	@echo "$(GREEN)Starting Docker containers...$(NC)"
	@docker-compose up -d
	@echo "$(GREEN)Docker services:$(NC)"
	@echo "  - PostgreSQL: localhost:5443"
	@echo "  - Redis: localhost:6398"
	@echo "  - Mailpit UI: http://localhost:8028"
	@echo "  - MinIO Console: http://localhost:9001"

## Start backend (FastAPI with auto-reload)
start-backend:
	@echo "$(GREEN)Starting backend API...$(NC)"
	@PYTHONPATH=src uv run uvicorn app:app --reload --host 0.0.0.0 --port 8001

## Start Celery worker for background tasks (reports queue)
queue:
	@echo "$(GREEN)Starting Celery worker for reports queue...$(NC)"
	@DYLD_FALLBACK_LIBRARY_PATH="$$(brew --prefix 2>/dev/null)/lib" PYTHONPATH=. uv run celery -A core.celery worker -Q reports -l INFO

## Start Celery worker in background
start-queue-bg:
	@echo "$(GREEN)Starting Celery worker in background...$(NC)"
	@DYLD_FALLBACK_LIBRARY_PATH="$$(brew --prefix 2>/dev/null)/lib" PYTHONPATH=. uv run celery -A core.celery worker -Q reports -l INFO > /tmp/celery-dsm.log 2>&1 &
	@echo "  - Celery queues: reports"
	@echo "  - Celery logs: /tmp/celery-dsm.log"

## Start frontend (Vite dev server)
start-frontend:
	@echo "$(GREEN)Starting frontend...$(NC)"
	@cd web/app && npm run dev

## Start frontend in background
start-frontend-bg:
	@echo "$(GREEN)Starting frontend in background...$(NC)"
	@cd web/app && npm run dev > /tmp/frontend-dsm.log 2>&1 &
	@echo "  - Frontend: http://localhost:5173"
	@echo "  - Frontend logs: /tmp/frontend-dsm.log"

# =============================================================================
# Installation
# =============================================================================

## Install dependencies (backend + frontend)
install:
	@echo "$(GREEN)Installing backend dependencies...$(NC)"
	@uv sync --all-extras
	@echo "$(GREEN)Installing frontend dependencies...$(NC)"
	@cd web/app && npm install

# =============================================================================
# Database
# =============================================================================

## Create new migration
db-migrate:
	@echo "$(GREEN)Creating new migration...$(NC)"
	@PYTHONPATH=src alembic revision --autogenerate -m "$(msg)"

## Apply database migrations
db-upgrade:
	@echo "$(GREEN)Applying migrations...$(NC)"
	@PYTHONPATH=src alembic upgrade head

## Downgrade database by one revision
db-downgrade:
	@echo "$(YELLOW)Downgrading database...$(NC)"
	@PYTHONPATH=src alembic downgrade -1

# =============================================================================
# Testing
# =============================================================================

## Run unit tests
test:
	@echo "$(GREEN)Running unit tests...$(NC)"
	@PYTHONPATH=src uv run pytest tests/unit/ -v

## Run integration tests (requires Docker PostgreSQL running)
test-integration:
	@echo "$(GREEN)Running integration tests...$(NC)"
	@PYTHONPATH=src uv run pytest tests/integration/ -v

## Run all tests
test-all:
	@echo "$(GREEN)Running all tests...$(NC)"
	@PYTHONPATH=src uv run pytest tests/ -v

# =============================================================================
# Code Quality
# =============================================================================

## Run linters
lint:
	@echo "$(GREEN)Running linters...$(NC)"
	@PYTHONPATH=src uv run mypy src/
	@uv run flake8 src/

## Run OWASP ZAP API scan (requires backend running on port 8000)
scan:
	@echo "$(GREEN)Running OWASP ZAP API scan against http://localhost:8001...$(NC)"
	@echo "$(YELLOW)Make sure the backend is running (make start-backend)$(NC)"
	@docker run --rm -t \
		--add-host=host.docker.internal:host-gateway \
		-v /tmp:/zap/wrk \
		ghcr.io/zaproxy/zaproxy:stable \
		zap-api-scan.py \
		-t http://host.docker.internal:8000/openapi.json \
		-f openapi \
		-J report.json 2>&1 | tee /tmp/zap-report-dsm.txt
	@echo "$(GREEN)Scan complete. Console output saved to /tmp/zap-report-dsm.txt$(NC)"
	@echo "$(GREEN)JSON report saved to /tmp/report.json$(NC)"

# =============================================================================
# Utilities
# =============================================================================

## Seed database with demo data
seed:
	@echo "$(GREEN)Seeding demo data...$(NC)"
	@PYTHONPATH=src uv run python scripts/seed_demo_data.py

## Reset database and seed fresh demo data
demo-reset:
	@echo "$(YELLOW)Resetting database...$(NC)"
	@PYTHONPATH=src alembic downgrade base
	@PYTHONPATH=src alembic upgrade head
	@echo "$(GREEN)Seeding demo data...$(NC)"
	@PYTHONPATH=src uv run python scripts/seed_demo_data.py

## Show logs from Docker containers
logs:
	@docker-compose logs -f

## Clean up generated files
clean:
	@echo "$(YELLOW)Cleaning up...$(NC)"
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	@echo "$(GREEN)Cleanup complete$(NC)"

# =============================================================================
# Help
# =============================================================================

## Show available commands
help:
	@echo "Available commands:"
	@echo ""
	@echo "  $(GREEN)make start$(NC)          - Start all services (Docker + Backend + Celery + Frontend)"
	@echo "  $(GREEN)make stop$(NC)           - Stop all services"
	@echo ""
	@echo "  $(GREEN)make start-docker$(NC)   - Start Docker containers only"
	@echo "  $(GREEN)make start-backend$(NC)  - Start backend API only"
	@echo "  $(GREEN)make start-frontend$(NC) - Start frontend dev server only"
	@echo "  $(GREEN)make queue$(NC)          - Start Celery worker (reports queue)"
	@echo ""
	@echo "  $(GREEN)make install$(NC)        - Install dependencies"
	@echo "  $(GREEN)make db-upgrade$(NC)     - Apply database migrations"
	@echo "  $(GREEN)make db-migrate$(NC)     - Create new migration (msg=description)"
	@echo ""
	@echo "  $(GREEN)make test$(NC)           - Run unit tests"
	@echo "  $(GREEN)make test-integration$(NC) - Run integration tests (requires Docker)"
	@echo "  $(GREEN)make test-all$(NC)       - Run all tests"
	@echo "  $(GREEN)make lint$(NC)           - Run linters"
	@echo "  $(GREEN)make scan$(NC)           - Run OWASP ZAP API security scan"
	@echo "  $(GREEN)make seed$(NC)           - Seed database with demo data"
	@echo "  $(GREEN)make demo-reset$(NC)     - Reset DB and seed fresh demo data"
	@echo "  $(GREEN)make logs$(NC)           - Show Docker logs"
	@echo "  $(GREEN)make clean$(NC)          - Clean generated files"
	@echo ""
	@echo "Services:"
	@echo "  - Frontend:       http://localhost:5173"
	@echo "  - Backend API:    http://localhost:8001"
	@echo "  - API Docs:       http://localhost:8001/docs"
	@echo "  - Mailpit:        http://localhost:8028"
	@echo "  - MinIO Console:  http://localhost:9001"
	@echo ""
	@echo "Staging API:"
	@echo "  - URL: https://staging.desksupportmonkey.com"
	@echo "  - Setup: sudo bash deploy/staging/setup.sh (on server)"
	@echo "  - Add remote: git remote add staging deploy@<server-ip>:/opt/dsm-staging/repo.git"
	@echo "  - Deploy: git push staging main"
	@echo "  - Frontend devs: cp web/app/.env.staging web/app/.env.local"
