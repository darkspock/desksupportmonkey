# Technical Design: E18 — Knowledge Base & Self-Service

**Epic:** [requirements.md](requirements.md)
**Date:** 2026-02-23
**Bounded Context:** `kb_bc`

## 1. Domain Layer

### 1.1 Enums

**File:** `src/kb_bc/article/domain/enums.py`

```python
class ArticleStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"

VALID_ARTICLE_STATUS_TRANSITIONS: dict[ArticleStatus, list[ArticleStatus]] = {
    ArticleStatus.DRAFT: [ArticleStatus.PUBLISHED],
    ArticleStatus.PUBLISHED: [ArticleStatus.DRAFT, ArticleStatus.ARCHIVED],
    ArticleStatus.ARCHIVED: [ArticleStatus.DRAFT],
}
```

### 1.2 Entities

**File:** `src/kb_bc/article/domain/entities.py`

```python
@dataclass
class Article:
    id: str
    company_id: str
    title: str
    slug: str
    content: str  # HTML from TipTap
    excerpt: Optional[str]
    category_id: Optional[str]
    status: ArticleStatus
    author_id: str
    view_count: int
    published_at: Optional[datetime]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    @classmethod
    def create(cls, company_id, title, content, author_id, ...) -> "Article": ...
    def publish(self) -> None: ...
    def unpublish(self) -> None: ...
    def archive(self) -> None: ...
    def restore(self) -> None: ...
    def update_content(self, title, content, excerpt) -> None: ...
    def increment_view_count(self) -> None: ...

@dataclass
class ArticleCategory:
    id: str
    company_id: str
    name: str
    slug: str
    description: Optional[str]
    sort_order: int
    created_at: Optional[datetime]

    @classmethod
    def create(cls, company_id, name, description, sort_order) -> "ArticleCategory": ...

@dataclass
class ArticleVersion:
    id: str
    article_id: str
    version_number: int
    title: str
    content: str
    edited_by: str
    created_at: Optional[datetime]
```

### 1.3 Repository Interface

**File:** `src/kb_bc/article/domain/repository.py`

```python
class ArticleRepositoryInterface(ABC):
    # Articles
    @abstractmethod
    def save(self, article: Article) -> None: ...
    @abstractmethod
    def find_by_id(self, article_id: str, company_id: str) -> Optional[Article]: ...
    @abstractmethod
    def find_by_slug(self, slug: str, company_id: str) -> Optional[Article]: ...
    @abstractmethod
    def find_all(self, company_id: str, filters: dict) -> tuple[list[Article], int]: ...
    @abstractmethod
    def find_published(self, company_id: str, filters: dict) -> tuple[list[Article], int]: ...
    @abstractmethod
    def delete(self, article_id: str, company_id: str) -> None: ...
    @abstractmethod
    def search(self, company_id: str, query: str, limit: int = 20) -> list[Article]: ...
    @abstractmethod
    def suggest(self, company_id: str, text: str, limit: int = 5) -> list[Article]: ...

    # Versions
    @abstractmethod
    def save_version(self, version: ArticleVersion) -> None: ...
    @abstractmethod
    def get_versions(self, article_id: str) -> list[ArticleVersion]: ...
    @abstractmethod
    def get_latest_version_number(self, article_id: str) -> int: ...

    # Categories
    @abstractmethod
    def save_category(self, category: ArticleCategory) -> None: ...
    @abstractmethod
    def find_category_by_id(self, category_id: str, company_id: str) -> Optional[ArticleCategory]: ...
    @abstractmethod
    def find_all_categories(self, company_id: str) -> list[ArticleCategory]: ...
    @abstractmethod
    def delete_category(self, category_id: str, company_id: str) -> None: ...
    @abstractmethod
    def count_articles_in_category(self, category_id: str) -> int: ...
```

### 1.4 Domain Exceptions

**File:** `src/kb_bc/article/domain/exceptions.py`

```python
class ArticleNotFoundError(Exception): ...
class InvalidArticleStatusTransitionError(Exception): ...
class ArticleDraftOnlyDeleteError(Exception): ...
class CategoryNotFoundError(Exception): ...
class CategoryHasArticlesError(Exception): ...
class DuplicateSlugError(Exception): ...
```

## 2. Application Layer

### 2.1 Commands (F0)

| File | Command | Handler |
|------|---------|---------|
| `create_article.py` | CreateArticleCommand | Creates Article entity, saves, creates version 1 |
| `update_article.py` | UpdateArticleCommand | Updates content, creates new version |
| `delete_article.py` | DeleteArticleCommand | Deletes draft article only |
| `publish_article.py` | PublishArticleCommand | Changes status to published |
| `unpublish_article.py` | UnpublishArticleCommand | Changes status back to draft |
| `archive_article.py` | ArchiveArticleCommand | Changes status to archived |
| `restore_article.py` | RestoreArticleCommand | Changes status from archived to draft |

### 2.2 Commands (F0 — Categories)

| File | Command | Handler |
|------|---------|---------|
| `create_category.py` | CreateCategoryCommand | Creates ArticleCategory |
| `update_category.py` | UpdateCategoryCommand | Updates category details |
| `delete_category.py` | DeleteCategoryCommand | Deletes category (if no articles) |

### 2.3 Queries (F0)

| File | Query | Returns |
|------|-------|---------|
| `list_articles.py` | ListArticlesQuery | tuple[list[ArticleListDto], int] |
| `get_article_detail.py` | GetArticleDetailQuery | ArticleDetailDto |
| `list_categories.py` | ListCategoriesQuery | list[CategoryDto] |

### 2.4 Queries (F1 — Version History)

| File | Query | Returns |
|------|-------|---------|
| `get_article_versions.py` | GetArticleVersionsQuery | list[ArticleVersionDto] |

### 2.5 Queries (F2 — Search & Self-Service)

| File | Query | Returns |
|------|-------|---------|
| `search_articles.py` | SearchArticlesQuery | list[ArticleListDto] |
| `list_public_articles.py` | ListPublicArticlesQuery | tuple[list[ArticleListDto], int] |
| `suggest_articles.py` | SuggestArticlesQuery | list[ArticleListDto] |

### 2.6 DTOs

```python
@dataclass
class ArticleListDto:
    id: str
    title: str
    slug: str
    excerpt: Optional[str]
    category_id: Optional[str]
    category_name: Optional[str]
    status: str
    author_id: str
    author_name: Optional[str]
    view_count: int
    published_at: Optional[datetime]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

@dataclass
class ArticleDetailDto:
    id: str
    title: str
    slug: str
    content: str
    excerpt: Optional[str]
    category_id: Optional[str]
    category_name: Optional[str]
    status: str
    author_id: str
    author_name: Optional[str]
    view_count: int
    published_at: Optional[datetime]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

@dataclass
class CategoryDto:
    id: str
    name: str
    slug: str
    description: Optional[str]
    sort_order: int
    article_count: int

@dataclass
class ArticleVersionDto:
    id: str
    version_number: int
    title: str
    content: str
    edited_by: str
    editor_name: Optional[str]
    created_at: Optional[datetime]
```

## 3. Infrastructure Layer

### 3.1 ORM Models

**File:** `src/kb_bc/article/infrastructure/models.py`

3 models: `ArticleModel`, `ArticleCategoryModel`, `ArticleVersionModel`

Key indexes:
- `ix_articles_company_status` (company_id, status)
- `ix_articles_company_category` (company_id, category_id)
- `ix_articles_company_slug` (company_id, slug) — UNIQUE
- `ix_articles_search_vector` — GIN index on search_vector column
- `ix_article_categories_company` (company_id)
- `uq_article_categories_company_slug` (company_id, slug) — UNIQUE
- `ix_article_versions_article` (article_id)

### 3.2 Full-Text Search

The `search_vector` column on `ArticleModel` is a `TSVector` type maintained via a database trigger or updated on save:

```python
from sqlalchemy import func
# On save/update:
article.search_vector = func.to_tsvector('english',
    func.coalesce(article.title, '') + ' ' + func.coalesce(article.content, ''))
```

For querying:
```python
query = query.where(
    ArticleModel.search_vector.match(search_term)
).order_by(
    func.ts_rank(ArticleModel.search_vector,
        func.plainto_tsquery('english', search_term)).desc()
)
```

### 3.3 Database Migration

**File:** `alembic/versions/z3b4c5d6e7f8_create_kb_tables.py`

Tables:
1. `article_categories` — KB categories
2. `articles` — Main article entries with tsvector column
3. `article_versions` — Version snapshots

### 3.4 Slug Generation

```python
import re
def generate_slug(title: str) -> str:
    slug = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')
    return slug[:120]  # Truncate for safety
```

Collision handling in repository: append `-2`, `-3`, etc. if slug exists.

## 4. HTTP Layer

### 4.1 Router Organization

```
adapters/http/api/kb/
├── __init__.py
├── routers.py
├── schemas.py
└── dependencies.py
```

### 4.2 Endpoint Summary

| Method | Path | Role | Feature |
|--------|------|------|---------|
| POST | /api/v1/kb/articles | technician+ | F0 |
| GET | /api/v1/kb/articles | technician+ | F0 |
| GET | /api/v1/kb/articles/:id | any auth | F0 |
| PUT | /api/v1/kb/articles/:id | technician+ | F0 |
| DELETE | /api/v1/kb/articles/:id | admin | F0 |
| POST | /api/v1/kb/articles/:id/publish | admin | F0 |
| POST | /api/v1/kb/articles/:id/unpublish | admin | F0 |
| POST | /api/v1/kb/articles/:id/archive | admin | F0 |
| POST | /api/v1/kb/articles/:id/restore | admin | F0 |
| GET | /api/v1/kb/articles/:id/versions | technician+ | F1 |
| POST | /api/v1/kb/categories | admin | F0 |
| GET | /api/v1/kb/categories | any auth | F0 |
| PUT | /api/v1/kb/categories/:id | admin | F0 |
| DELETE | /api/v1/kb/categories/:id | admin | F0 |
| GET | /api/v1/kb/search | any auth | F2 |
| GET | /api/v1/kb/public | employee+ | F2 |
| GET | /api/v1/kb/suggest | employee+ | F3 |

## 5. Frontend Architecture

### 5.1 Pages

| Page | Path | Role | Feature |
|------|------|------|---------|
| KBArticleListPage | /kb | technician+ | F0 |
| KBArticleDetailPage | /kb/articles/:id | any auth | F0 |
| CreateArticlePage | /kb/articles/new | technician+ | F0 |
| EditArticlePage | /kb/articles/:id/edit | technician+ | F0 |
| KBArticleVersionsPage | /kb/articles/:id/versions | technician+ | F1 |
| KBSearchPage | /kb/search | any auth | F2 |
| KBPublicPage | /knowledge-base | employee+ | F2 |

### 5.2 TipTap Editor

Install packages:
```bash
npm install @tiptap/react @tiptap/starter-kit @tiptap/extension-link @tiptap/extension-image @tiptap/extension-code-block-lowlight @tiptap/extension-placeholder
```

Component: `web/app/src/components/editor/TipTapEditor.tsx`
- Toolbar with bold, italic, headings, bullet list, ordered list, code block, link, image
- Outputs HTML content

### 5.3 Sidebar Navigation

Under new "Knowledge" section:
- Knowledge Base → /kb (technician+)

Under "Self-Service" or employee nav:
- Knowledge Base → /knowledge-base (employee+)

## 6. Testing Strategy

### 6.1 Unit Tests

| Test File | What It Tests |
|-----------|---------------|
| `tests/unit/kb_bc/article/domain/test_entities.py` | Entity creation, status transitions, slug generation |
| `tests/unit/kb_bc/article/application/commands/test_create_article.py` | Create command handler |
| `tests/unit/kb_bc/article/application/commands/test_publish_article.py` | Publish command handler |
| `tests/unit/kb_bc/article/application/queries/test_list_articles.py` | List query handler |

### 6.2 Integration Tests

**File:** `tests/integration/test_kb_endpoints.py`

Coverage: All CRUD operations, status transitions, categories, versions, search, public access, authorization.

## 7. Implementation Order

**Phase 1: F0 — KB Foundation** (Domain → Infra → App → HTTP → Tests → FE with TipTap)
**Phase 2: F1 — Version History** (Version query → HTTP → FE)
**Phase 3: F2 — Search & Self-Service** (tsvector → Search query → Public endpoint → FE)
**Phase 4: F3 — AI Suggestions** (Suggest endpoint → Ticket creation integration)

## 8. Collateral Changes

| File | Component | Change | Feature |
|------|-----------|--------|---------|
| `app.py` | Router registration | Add KB router | F0 |
| `web/app/src/router.tsx` | Routes | Add KB pages | F0 |
| `web/app/src/components/layout/Sidebar.tsx` | Navigation | Add KB entries | F0 |
| `web/app/src/locales/en.ts` | i18n | KB translations | F0 |
| `web/app/src/locales/es.ts` | i18n | KB translations | F0 |
| `web/app/src/types/index.ts` | Types | KB interfaces | F0 |
| `web/app/package.json` | Dependencies | TipTap packages | F0 |
