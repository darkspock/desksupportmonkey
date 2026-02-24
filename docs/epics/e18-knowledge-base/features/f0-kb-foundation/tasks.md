# Tasks: F0 — KB Foundation

**Feature:** [requirements.md](../../requirements.md)
**Design:** [../../design.md](../../design.md)
**Date:** 2026-02-23

## Summary

| # | Task | Complexity | Phase |
|---|------|-----------|-------|
| 1 | Domain: enums | S | Domain |
| 2 | Domain: entities (Article, ArticleCategory, ArticleVersion) | M | Domain |
| 3 | Domain: repository interface | S | Domain |
| 4 | Domain: exceptions | S | Domain |
| 5 | Infrastructure: ORM models | M | Infra |
| 6 | Infrastructure: Alembic migration | S | Infra |
| 7 | Infrastructure: repository implementation | L | Infra |
| 8 | Application: CreateArticleCommand + handler | S | App |
| 9 | Application: UpdateArticleCommand + handler | S | App |
| 10 | Application: DeleteArticleCommand + handler | S | App |
| 11 | Application: PublishArticleCommand + handler | S | App |
| 12 | Application: UnpublishArticleCommand + handler | S | App |
| 13 | Application: ArchiveArticleCommand + handler | S | App |
| 14 | Application: RestoreArticleCommand + handler | S | App |
| 15 | Application: CreateCategoryCommand + handler | S | App |
| 16 | Application: UpdateCategoryCommand + handler | S | App |
| 17 | Application: DeleteCategoryCommand + handler | S | App |
| 18 | Application: ListArticlesQuery + handler | S | App |
| 19 | Application: GetArticleDetailQuery + handler | S | App |
| 20 | Application: ListCategoriesQuery + handler | S | App |
| 21 | HTTP: dependencies, schemas | M | HTTP |
| 22 | HTTP: article routers (CRUD + status actions) | M | HTTP |
| 23 | HTTP: category routers | S | HTTP |
| 24 | Register router in app.py | S | HTTP |
| 25 | Unit tests: domain entities | M | Test |
| 26 | Unit tests: command handlers | M | Test |
| 27 | Integration tests: endpoints | M | Test |
| 28 | Frontend: Install TipTap + create editor component | M | FE |
| 29 | Frontend: KBArticleListPage | M | FE |
| 30 | Frontend: KBArticleDetailPage | M | FE |
| 31 | Frontend: CreateArticlePage (with TipTap) | M | FE |
| 32 | Frontend: EditArticlePage (with TipTap) | M | FE |
| 33 | Frontend: routes + sidebar entry | S | FE |
| 34 | i18n: KB translations EN/ES | S | FE |
| 35 | TypeScript types in types/index.ts | S | FE |

## Detailed Tasks

### Task 1: Enums
- **File:** `src/kb_bc/article/domain/enums.py`
- **What:** ArticleStatus (draft/published/archived), VALID_ARTICLE_STATUS_TRANSITIONS
- [x] Done

### Task 2: Entities
- **File:** `src/kb_bc/article/domain/entities.py`
- **What:** Article (create, publish, unpublish, archive, restore, update_content, increment_view_count), ArticleCategory (create), ArticleVersion
- [x] Done

### Task 3: Repository interface
- **File:** `src/kb_bc/article/domain/repository.py`
- **What:** ArticleRepositoryInterface with all abstract methods for articles, versions, categories
- [x] Done

### Task 4: Exceptions
- **File:** `src/kb_bc/article/domain/exceptions.py`
- **What:** ArticleNotFoundError, InvalidArticleStatusTransitionError, ArticleDraftOnlyDeleteError, CategoryNotFoundError, CategoryHasArticlesError, DuplicateSlugError
- [x] Done

### Task 5: ORM models
- **File:** `src/kb_bc/article/infrastructure/models.py`
- **What:** ArticleModel, ArticleCategoryModel, ArticleVersionModel with Mapped annotations + indexes
- [x] Done

### Task 6: Alembic migration
- **File:** `alembic/versions/z3b4c5d6e7f8_create_kb_tables.py`
- **What:** Create article_categories, articles, article_versions tables
- [x] Done

### Task 7: Repository implementation
- **File:** `src/kb_bc/article/infrastructure/repository.py`
- **What:** ArticleRepository implementing all interface methods. Slug collision handling. tsvector update on save.
- [x] Done

### Task 8: CreateArticleCommand
- **File:** `src/kb_bc/article/application/commands/create_article.py`
- **What:** CreateArticleCommand(company_id, title, content, author_id, ...) + handler. Creates Article, saves, creates version 1.
- [x] Done

### Task 9: UpdateArticleCommand
- **File:** `src/kb_bc/article/application/commands/update_article.py`
- **What:** UpdateArticleCommand(article_id, company_id, title, content, ...) + handler. Updates article, creates new version.
- [x] Done

### Task 10: DeleteArticleCommand
- **File:** `src/kb_bc/article/application/commands/delete_article.py`
- **What:** DeleteArticleCommand(article_id, company_id) + handler. Only drafts can be deleted.
- [x] Done

### Task 11: PublishArticleCommand
- **File:** `src/kb_bc/article/application/commands/publish_article.py`
- **What:** PublishArticleCommand(article_id, company_id) + handler. Validates transition, sets published_at.
- [x] Done

### Task 12: UnpublishArticleCommand
- **File:** `src/kb_bc/article/application/commands/unpublish_article.py`
- **What:** UnpublishArticleCommand(article_id, company_id) + handler. Reverts to draft.
- [x] Done

### Task 13: ArchiveArticleCommand
- **File:** `src/kb_bc/article/application/commands/archive_article.py`
- **What:** ArchiveArticleCommand(article_id, company_id) + handler. Archives published article.
- [x] Done

### Task 14: RestoreArticleCommand
- **File:** `src/kb_bc/article/application/commands/restore_article.py`
- **What:** RestoreArticleCommand(article_id, company_id) + handler. Restores archived to draft.
- [x] Done

### Task 15: CreateCategoryCommand
- **File:** `src/kb_bc/article/application/commands/create_category.py`
- **What:** CreateCategoryCommand(company_id, name, description, sort_order) + handler.
- [x] Done

### Task 16: UpdateCategoryCommand
- **File:** `src/kb_bc/article/application/commands/update_category.py`
- **What:** UpdateCategoryCommand(category_id, company_id, name, ...) + handler.
- [x] Done

### Task 17: DeleteCategoryCommand
- **File:** `src/kb_bc/article/application/commands/delete_category.py`
- **What:** DeleteCategoryCommand(category_id, company_id) + handler. Fails if category has articles.
- [x] Done

### Task 18: ListArticlesQuery
- **File:** `src/kb_bc/article/application/queries/list_articles.py`
- **What:** ListArticlesQuery(company_id, page, page_size, status, category_id, search) + handler.
- [x] Done

### Task 19: GetArticleDetailQuery
- **File:** `src/kb_bc/article/application/queries/get_article_detail.py`
- **What:** GetArticleDetailQuery(article_id, company_id, increment_view) + handler. Returns ArticleDetailDto.
- [x] Done

### Task 20: ListCategoriesQuery
- **File:** `src/kb_bc/article/application/queries/list_categories.py`
- **What:** ListCategoriesQuery(company_id) + handler. Returns list[CategoryDto] with article_count.
- [x] Done

### Task 21: HTTP schemas + dependencies
- **Files:** `adapters/http/api/kb/schemas.py`, `adapters/http/api/kb/dependencies.py`
- **What:** Request/response schemas. get_article_repo dependency.
- [x] Done

### Task 22: Article routers
- **File:** `adapters/http/api/kb/routers.py`
- **What:** CRUD endpoints + publish/unpublish/archive/restore actions.
- [x] Done

### Task 23: Category routers
- **File:** `adapters/http/api/kb/routers.py` (same file)
- **What:** Category CRUD endpoints.
- [x] Done

### Task 24: Register router
- **File:** `app.py`
- **What:** Import and include KB router.
- [x] Done

### Task 25: Unit tests — domain entities
- **File:** `tests/unit/kb_bc/article/domain/test_entities.py`
- **What:** Test Article creation, status transitions, slug generation, view count.
- [x] Done

### Task 26: Unit tests — command handlers
- **File:** `tests/unit/kb_bc/article/application/`
- **What:** Test create, update, publish, delete command handlers.
- [x] Done

### Task 27: Integration tests
- **File:** `tests/integration/test_kb_endpoints.py`
- **What:** Test all CRUD, status transitions, categories, authorization.
- [x] Done

### Task 28: TipTap editor component
- **Files:** `web/app/src/components/editor/TipTapEditor.tsx` (NEW)
- **What:** Install TipTap packages. Create reusable editor component with toolbar.
- [x] Done

### Task 29: KBArticleListPage
- **File:** `web/app/src/pages/technician/KBArticleListPage.tsx` (NEW)
- **What:** List page with filters (status, category, search). Table with title, category, status badge, author, dates.
- [x] Done

### Task 30: KBArticleDetailPage
- **File:** `web/app/src/pages/technician/KBArticleDetailPage.tsx` (NEW)
- **What:** Detail page showing article content rendered as HTML. Status badge. Action buttons (publish/archive/edit/delete).
- [x] Done

### Task 31: CreateArticlePage
- **File:** `web/app/src/pages/technician/CreateArticlePage.tsx` (NEW)
- **What:** Form with title, excerpt, category select, TipTap editor for content. Save as draft.
- [x] Done

### Task 32: EditArticlePage
- **File:** `web/app/src/pages/technician/EditArticlePage.tsx` (NEW)
- **What:** Same form as create but pre-filled. Update on save.
- [x] Done

### Task 33: Routes + sidebar
- **Files:** `web/app/src/router.tsx`, `web/app/src/components/layout/Sidebar.tsx`
- **What:** Route /kb (technician+), /kb/articles/new, /kb/articles/:id, /kb/articles/:id/edit. Sidebar entry under Knowledge section.
- [x] Done

### Task 34: i18n translations
- **Files:** `web/app/src/locales/en.ts`, `es.ts`
- **What:** All page.kb.* keys and nav.knowledge_base.
- [x] Done

### Task 35: TypeScript types
- **File:** `web/app/src/types/index.ts`
- **What:** Article, ArticleCategory, ArticleVersion, ArticleListItem interfaces.
- [x] Done
