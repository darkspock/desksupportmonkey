# Slicing: E17 - Scheduled Maintenance

**Epic:** [requirements.md](requirements.md)
**Date:** 2026-02-18
**Total Features:** 4

## Dependency Graph

```text
F0: Domain & Infrastructure
 ├── F1: Maintenance Lifecycle
 ├── F2: Templates & Recurring Plans
 └── F3: Frontend (depends on F1 + F2)
```

## Features Summary

| # | Feature | Covers | Complexity | Depends | Status |
|---|---------|--------|------------|---------|--------|
| F0 | Domain & Infrastructure | Entities, enums, migrations, repos, domain tests | Medium | None | Done |
| F1 | Maintenance Lifecycle | Record CRUD, transitions, notifications, Celery reminders | High | F0 | Done |
| F2 | Templates & Recurring Plans | Template CRUD, plan apply, recurring generator | Medium | F0 | Done |
| F3 | Frontend | Pages, routing, sidebar, i18n, dashboard/asset collateral | High | F1, F2 | Done |
