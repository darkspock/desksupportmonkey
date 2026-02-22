# CTO — Co-founder

## Role Summary

The CTO owns everything technical and has made a deliberate bet: AI is not a tool, it's the operating model. Every part of the engineering workflow — requirements, design, implementation, testing, review, deployment — is built around AI-assisted execution. The goal is to ship at a pace that would be impossible with a traditional team, without sacrificing architecture quality or code correctness.

This is not about using AI as autocomplete. It's about designing a process where AI handles the bulk of implementation, and the CTO's job is to define clear specifications, enforce architectural boundaries, and validate output.

Speed and quality are not in tension here — they are the same thing. Shipping fast with bugs is not shipping fast. A defect in production costs more to fix than the feature cost to build. The quality gate is non-negotiable.

---

## AI-First Engineering Model

### How the team builds
- **Requirements → specs**: CEO provides business context, CTO produces structured technical specs and tasks documents that AI agents can execute against
- **Implementation**: AI agents (Claude Code, Cursor, Copilot) implement features from task documents — the CTO reviews and merges
- **Testing**: AI generates unit and integration tests from spec; CTO validates coverage and edge cases
- **Code review**: AI-assisted review catches style, type errors, and architectural violations before human review
- **Documentation**: AI drafts all technical docs, ADRs, and API specs from code and requirements

### Principles
- A feature is only ready to implement when the spec is unambiguous enough for an AI to execute it without guessing
- Every architectural decision is documented so AI context is consistent across sessions
- `CLAUDE.md`, `architecture.md`, and `tasks.md` are first-class artifacts — not afterthoughts
- The CTO never writes boilerplate. If it's boilerplate, it's delegated to AI.

### Quality Gates (non-negotiable)
- **Zero bugs shipped to production** — every feature requires passing unit tests, integration tests, mypy, and flake8 before merge
- **No exceptions to the test requirement** — if there is no test, the feature is not done
- **Type safety is mandatory** — mypy strict mode, no `Any`, no suppressed errors
- **AI output is always reviewed** — speed comes from better specs, not from skipping review
- **Architectural violations are reverted** — a shortcut that breaks DDD/CQRS boundaries is not a shortcut, it's debt that compounds
- **No "fix it later"** — later never comes in a bootstrapped company; fix it now or don't ship it
- **/check-architecture and /check-quality run on every feature** before marking it done

---

## Responsibilities

### Architecture & Standards
- Design and own the system architecture (FastAPI, DDD, CQRS, PostgreSQL, React)
- Define and enforce coding standards via `CLAUDE.md` and architecture docs
- Make final decisions on framework choices, data model, and API design
- Ensure AI-generated code respects architectural boundaries (bounded contexts, clean layers)

### AI Workflow Design
- Define and continuously improve the AI development pipeline (requirements → design → tasks → implementation → review)
- Maintain context documents that keep AI agents aligned across sessions
- Evaluate and adopt new AI tools as they emerge — this is an ongoing competitive advantage
- Train the Senior Engineer to work effectively with AI tools

### Product
- Translate CEO priorities into structured epics, features, and task documents
- Own the product backlog and sprint cadence
- Prioritize technical debt vs. features based on customer impact

### Infrastructure & DevOps
- Own deployments, uptime, and incident response
- Manage production and staging environments
- Define monitoring strategy (Sentry, health checks, alerting)

### Security & Compliance
- Own GDPR compliance and data security posture
- Manage secrets, access controls, and environment configuration

---

## Skills Required

- Python (FastAPI, SQLAlchemy, Alembic, Celery) — deep
- TypeScript + React — strong
- PostgreSQL, Redis — strong
- Linux, Nginx, systemd, CI/CD — solid
- DDD, CQRS, clean architecture — non-negotiable
- Expert-level AI tooling (Claude Code, Cursor or equivalent) — this is the core skill
- Ability to write specs precise enough that AI can implement them correctly

---

## Metrics Owned

- Features shipped per week
- **Bug escape rate to production — target: zero**
- System uptime
- Deployment frequency
- Test coverage (unit + integration)
- AI implementation acceptance rate (how often AI output is merged without major rework)
- mypy error count in CI — target: zero

---

## What This CTO Is Not

- Not the person who writes every line of code manually
- Not skeptical of AI-generated code — but rigorous about reviewing it
- Not building a team of 10 engineers when an AI-augmented team of 2 can outship them
- Not trading quality for speed — the philosophy is that good specs + AI + strict gates *are* the speed advantage
- Not shipping something broken because the sprint ends — the sprint ends when the quality bar is met
