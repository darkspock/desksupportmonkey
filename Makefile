.PHONY: start stop start-docker start-backend queue start-queue-bg install logs db-migrate db-upgrade test lint clean

# Colors for terminal output
GREEN := \033[0;32m
YELLOW := \033[0;33m
NC := \033[0m # No Color

# =============================================================================
# Main Commands
# =============================================================================

## Start all services (Docker + Backend + Celery)
start:
	@echo "$(GREEN)Starting all services...$(NC)"
	@make start-docker
	@echo "$(GREEN)Waiting for Docker services to be healthy...$(NC)"
	@sleep 3
	@make start-queue-bg
	@make start-backend

## Stop all services
stop:
	@echo "$(YELLOW)Stopping all services...$(NC)"
	@-pkill -f "uvicorn app:app" 2>/dev/null || true
	@-pkill -f "celery" 2>/dev/null || true
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
	@PYTHONPATH=src uv run uvicorn app:app --reload --host 0.0.0.0 --port 8000

## Start Celery worker for background tasks (reports queue)
queue:
	@echo "$(GREEN)Starting Celery worker for reports queue...$(NC)"
	@PYTHONPATH=. uv run celery -A core.celery worker -Q reports -l INFO

## Start Celery worker in background
start-queue-bg:
	@echo "$(GREEN)Starting Celery worker in background...$(NC)"
	@PYTHONPATH=. uv run celery -A core.celery worker -Q reports -l INFO > /tmp/celery-dsm.log 2>&1 &
	@echo "  - Celery queues: reports"
	@echo "  - Celery logs: /tmp/celery-dsm.log"

# =============================================================================
# Installation
# =============================================================================

## Install dependencies
install:
	@echo "$(GREEN)Installing dependencies...$(NC)"
	@uv sync --all-extras

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

## Run tests
test:
	@echo "$(GREEN)Running tests...$(NC)"
	@PYTHONPATH=src uv run pytest tests/ -v

# =============================================================================
# Code Quality
# =============================================================================

## Run linters
lint:
	@echo "$(GREEN)Running linters...$(NC)"
	@PYTHONPATH=src uv run mypy src/
	@uv run flake8 src/

# =============================================================================
# Utilities
# =============================================================================

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
	@echo "  $(GREEN)make start$(NC)          - Start all services (Docker + Backend + Celery)"
	@echo "  $(GREEN)make stop$(NC)           - Stop all services"
	@echo ""
	@echo "  $(GREEN)make start-docker$(NC)   - Start Docker containers only"
	@echo "  $(GREEN)make start-backend$(NC)  - Start backend API only"
	@echo "  $(GREEN)make queue$(NC)          - Start Celery worker (reports queue)"
	@echo ""
	@echo "  $(GREEN)make install$(NC)        - Install dependencies"
	@echo "  $(GREEN)make db-upgrade$(NC)     - Apply database migrations"
	@echo "  $(GREEN)make db-migrate$(NC)     - Create new migration (msg=description)"
	@echo ""
	@echo "  $(GREEN)make test$(NC)           - Run tests"
	@echo "  $(GREEN)make lint$(NC)           - Run linters"
	@echo "  $(GREEN)make logs$(NC)           - Show Docker logs"
	@echo "  $(GREEN)make clean$(NC)          - Clean generated files"
	@echo ""
	@echo "Services:"
	@echo "  - Backend API:    http://localhost:8000"
	@echo "  - API Docs:       http://localhost:8000/docs"
	@echo "  - Mailpit:        http://localhost:8028"
	@echo "  - MinIO Console:  http://localhost:9001"
