# DeskSupportMonkey AI Documentation

Development documentation for AI assistants working on the IT Service Desk & Asset Inventory platform.

## Quick Start

**ALWAYS read these first:**
1. [Critical Rules](architecture/critical-rules.md) - **MUST READ** before coding
2. [Agents README](agents/README.md) - Understand the development pipeline
3. [Working Documentation](working_documentation.md) - Requirement types (Epic/Feature/Hotfix/Case)

## Documentation Index

### Development Process
- **[Agents README](agents/README.md)** - 10-agent development pipeline
- **[Working Documentation](working_documentation.md)** - Requirement types (Epic/Feature/Hotfix/Case)
- **[Requirement Analysis Guide](requirement_analysis_guide.md)** - How to validate requirements

### Backend Architecture
- **[Critical Rules](architecture/critical-rules.md)** - MUST READ before any implementation
- **[Architecture](architecture/architecture.md)** - DDD, Clean Architecture overview
- **[Application Layer](architecture/application-layer.md)** - CQRS patterns, Commands, Queries
- **[Infrastructure](architecture/infrastructure.md)** - Repository patterns, persistence
- **[HTTP Layer](architecture/http-layer.md)** - API endpoints, controllers
- **[Code Quality](architecture/code-quality.md)** - SOLID, naming conventions

### Frontend Architecture
- **[Technical Architecture](architecture/frontend/TECHNICAL_ARCHITECTURE.md)** - React + TypeScript stack
- **[Coding Standards](architecture/frontend/CODING_STANDARDS.md)** - React/TypeScript best practices
- **[Component Library](architecture/frontend/COMPONENT_LIBRARY.md)** - shadcn/ui and custom components

## Claude Commands

| Command | Purpose |
|---------|---------|
| `/requirement-write` | Create requirement document |
| `/requirement-validate` | Validate requirement completeness |
| `/requirement-design` | Design technical solution |
| `/requirement-tasks` | Create implementation tasks |
| `/check-dod` | Verify definition of done |
| `/check-architecture` | Check architecture compliance |
| `/check-quality` | Check code quality |
| `/check-performance` | Check performance issues |
| `/linter` | Run linter/compile |
| `/testing` | Run and analyze tests |

## File Structure

```
ai_docs/
├── README.md                       # This file - Documentation index
├── working_documentation.md        # Requirement types & workflows
├── requirement_analysis_guide.md   # AI analysis instructions
│
├── agents/                         # 10 Agent definitions
│   ├── README.md                   # Agent pipeline overview
│   ├── 1. requirement_writer.md
│   ├── 2. requirement_validator.md
│   ├── 3. requirement_design_solution.md
│   ├── 4. requirement_make_tasks.md
│   ├── 5. check_definition_of_done.md
│   ├── 6. check_architecture.md
│   ├── 7. check_code_quality.md
│   ├── 8. check_performance.md
│   ├── 9. linter_compile.md
│   └── 10. testing.md
│
└── architecture/                   # Architecture guides
    ├── critical-rules.md           # MUST READ
    ├── architecture.md             # DDD overview
    ├── application-layer.md        # CQRS
    ├── infrastructure.md           # Repositories
    ├── http-layer.md               # API patterns
    ├── code-quality.md             # SOLID, naming
    └── frontend/                   # Frontend architecture
        ├── TECHNICAL_ARCHITECTURE.md
        ├── CODING_STANDARDS.md
        └── COMPONENT_LIBRARY.md
```

## Key Commands

```bash
# Development
make start           # Start all services
make stop            # Stop all services
make start-backend   # Start FastAPI backend
make queue           # Start Celery worker

# Database
make db-upgrade      # Apply migrations
make db-migrate msg="description"  # Create migration

# Testing & Quality
make test            # Run tests
make lint            # Run linters
```
