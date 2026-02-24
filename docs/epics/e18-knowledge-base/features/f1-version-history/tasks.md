# Tasks: F1 — Version History

**Feature:** [requirements.md](../../requirements.md)
**Design:** [../../design.md](../../design.md)
**Date:** 2026-02-23

## Summary

| # | Task | Complexity | Phase |
|---|------|-----------|-------|
| 1 | ArticleVersion entity | S | Domain |
| 2 | Version repository methods | S | Domain |
| 3 | ORM model (ArticleVersionModel) | S | Infra |
| 4 | save_version + get_versions in repository | S | Infra |
| 5 | GetArticleVersionsQuery + handler | S | App |
| 6 | GET /articles/:id/versions endpoint | S | HTTP |
| 7 | KBArticleVersionsPage frontend | M | FE |
| 8 | Unit tests | S | Test |

## Detailed Tasks

### Task 1: ArticleVersion entity
- **File:** `src/kb_bc/article/domain/entities.py`
- **What:** ArticleVersion dataclass with create() class method
- **Note:** Built during F0 implementation
- [x] Done

### Task 2: Version repository methods
- **File:** `src/kb_bc/article/domain/repository.py`
- **What:** save_version, get_versions, get_latest_version_number abstract methods
- **Note:** Built during F0 implementation
- [x] Done

### Task 3: ORM model
- **File:** `src/kb_bc/article/infrastructure/models.py`
- **What:** ArticleVersionModel with Mapped annotations
- **Note:** Built during F0 implementation
- [x] Done

### Task 4: Repository implementation
- **File:** `src/kb_bc/article/infrastructure/repository.py`
- **What:** save_version, get_versions, get_latest_version_number implementations
- **Note:** Built during F0 implementation
- [x] Done

### Task 5: GetArticleVersionsQuery
- **File:** `src/kb_bc/article/application/queries/get_article_versions.py`
- **What:** Query + handler with user name resolution
- **Note:** Built during F0 implementation
- [x] Done

### Task 6: Versions endpoint
- **File:** `adapters/http/api/kb/routers.py`
- **What:** GET /articles/{article_id}/versions (technician+)
- **Note:** Built during F0 implementation
- [x] Done

### Task 7: KBArticleVersionsPage
- **File:** `web/app/src/pages/technician/KBArticleVersionsPage.tsx`
- **What:** Version history page with expandable content details
- **Note:** Built during F0 implementation
- [x] Done

### Task 8: Unit tests
- **File:** `tests/unit/kb_bc/article/domain/test_entities.py`
- **What:** TestArticleVersion class with version creation test
- **Note:** Built during F0 implementation
- [x] Done
