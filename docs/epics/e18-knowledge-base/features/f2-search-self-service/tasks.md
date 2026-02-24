# Tasks: F2 — Search & Self-Service

**Feature:** [requirements.md](../../requirements.md)
**Design:** [../../design.md](../../design.md)
**Date:** 2026-02-23

## Summary

| # | Task | Complexity | Phase |
|---|------|-----------|-------|
| 1 | Search repository method | S | Infra |
| 2 | GET /search endpoint | S | HTTP |
| 3 | GET /public endpoint (published articles) | S | HTTP |
| 4 | KnowledgeBasePage (employee self-service) | M | FE |
| 5 | Route /knowledge-base + sidebar entry | S | FE |
| 6 | i18n keys for public KB | S | FE |

## Detailed Tasks

### Task 1: Search repository method
- **File:** `src/kb_bc/article/infrastructure/repository.py`
- **What:** search() using LIKE on title+content, ordered by view_count desc
- **Note:** Built during F0 implementation
- [x] Done

### Task 2: Search endpoint
- **File:** `adapters/http/api/kb/routers.py`
- **What:** GET /search (employee+) with query and limit params
- **Note:** Built during F0 implementation
- [x] Done

### Task 3: Public articles endpoint
- **File:** `adapters/http/api/kb/routers.py`
- **What:** GET /public (employee+) returns paginated published articles
- **Note:** Built during F0 implementation
- [x] Done

### Task 4: KnowledgeBasePage
- **File:** `web/app/src/pages/employee/KnowledgeBasePage.tsx`
- **What:** Employee-facing KB with card layout, search, category filter
- **Note:** Built during F0 implementation
- [x] Done

### Task 5: Route + sidebar entry
- **Files:** `web/app/src/router.tsx`, `Sidebar.tsx`
- **What:** /knowledge-base route for all users, sidebar entry in Knowledge section
- **Note:** Built during F0 implementation
- [x] Done

### Task 6: i18n keys
- **Files:** `web/app/src/locales/en.ts`, `es.ts`
- **What:** page.kb.public_title, public_subtitle, search_articles, no_articles_public
- **Note:** Built during F0 implementation
- [x] Done
