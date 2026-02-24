# Epic Slicing: E18 - Knowledge Base & Self-Service

**Epic:** [requirements.md](requirements.md)
**Date:** 2026-02-23
**Total Features:** 4

## Slicing Rationale

E18 introduces a new bounded context (`kb_bc`) with 3 entities (Article, ArticleCategory, ArticleVersion), a status workflow, rich text editing (TipTap), PostgreSQL full-text search, employee self-service portal, and AI article suggestions. The scope requires slicing into vertical features.

Slicing follows **vertical slices by user value**:
- **F0** establishes the foundation (BC, entities, CRUD, categories, TipTap editor, technician pages) — users can create and manage KB articles
- **F1** adds version history — edit tracking and audit capability
- **F2** adds full-text search and employee self-service — employees can find answers independently
- **F3** adds AI article suggestions on ticket creation — ticket deflection

Each feature is independently deployable and delivers standalone user value.

## Dependency Graph

```
Feature 0: KB Foundation
    │
    ├── Feature 1: Version History
    │
    ├── Feature 2: Search & Self-Service
    │
    └── Feature 3: AI Article Suggestions
```

All features depend only on F0. No circular or cross-feature dependencies.

## Features Summary

| # | Feature | Dependencies | Value Delivered | Complexity | Status |
|---|---------|--------------|-----------------|------------|--------|
| 0 | KB Foundation | None | Create, edit, and manage articles with TipTap rich text editor, categories, status workflow | L | Done |
| 1 | Version History | F0 | Version snapshots on every edit, version list with content | S | Done |
| 2 | Search & Self-Service | F0 | PostgreSQL full-text search, employee self-service KB portal | M | Done |
| 3 | AI Article Suggestions | F0 | Suggest matching KB articles when employee creates a ticket | S | Done |

## Recommended Order

1. **Feature 0: KB Foundation** — Must be first. Creates the BC, all core DB tables, Article entity, status workflow, category CRUD, TipTap editor component, CRUD endpoints, and primary frontend (list/detail/create/edit). All other features extend this.
2. **Feature 1: Version History** — Adds edit tracking. Version snapshots created on every article save. Simple query + frontend page.
3. **Feature 2: Search & Self-Service** — Adds full-text search and employee portal. PostgreSQL tsvector for ranked search results. Employee-facing pages to browse and search published articles.
4. **Feature 3: AI Article Suggestions** — Adds ticket deflection. When an employee types a ticket description, suggest matching published KB articles. Best built last when articles exist.

## Slicing Validation

- [x] No circular dependencies
- [x] Unidirectional dependency flow (all depend only on F0)
- [x] Each feature independently deployable
- [x] Vertical slices (not horizontal layers)
- [x] Shared foundation identified (F0)
- [x] No overlapping scope
- [x] Each feature delivers minimum viable value
- [x] All epic scope covered

## Risk Notes

- F0 is large (L complexity) because it includes the full article lifecycle + TipTap editor integration + categories + frontend. Consider splitting into sub-tasks.
- TipTap needs to be installed as a new npm dependency. Ensure compatibility with React 19.
- F2 PostgreSQL tsvector requires a GIN index and trigger/update logic. Test with large article volumes.
- F3 AI suggestion quality depends on article content being well-written and descriptive.
