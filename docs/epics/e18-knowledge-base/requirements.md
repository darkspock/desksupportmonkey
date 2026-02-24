# Epic E18: Knowledge Base & Self-Service

**Date:** 2026-02-23
**Priority:** High
**Status:** In Progress
**Bounded Context:** `kb_bc`

## Business Alignment

**Objective:** Provide a built-in knowledge base for IT support teams to document solutions, FAQs, and procedures, enabling employee self-service and reducing ticket volume through article deflection.

**KPI Targets:**
- 20% reduction in repetitive tickets through article deflection
- 80% of common issues have documented KB articles
- Average article usefulness rating > 4/5
- Employee self-service resolution rate > 30%

**Evidence:** ITIL Knowledge Management practice. Self-service portals are proven to reduce L1 ticket volume by 20-40%.

## Problem Statement

**Current situation:** Support knowledge exists only in technician heads or scattered documents. Employees cannot self-serve and must create tickets for every issue.

| Pain Point | Impact |
|-----------|--------|
| No centralized knowledge repository | Technicians repeatedly solve the same issues |
| No self-service portal | Employees must file tickets for known solutions |
| No article search | Cannot find existing solutions quickly |
| No version control for articles | Article edits have no history |
| No ticket deflection | Ticket volume unnecessarily high |

**Who is affected:**
- **Technicians:** Need to document and share solutions
- **Admins:** Need to manage knowledge base content and categories
- **Employees:** Need self-service access to solutions and FAQs

## Proposed Solution

A new `kb_bc` bounded context implementing a full knowledge base with:
1. Articles with rich text content (TipTap WYSIWYG editor)
2. Category and tag organization
3. Article status workflow (draft → published → archived)
4. Version history with full audit trail
5. PostgreSQL full-text search (tsvector)
6. Employee self-service portal
7. AI-suggested articles on ticket creation for deflection

### User Stories

**US1:** As a technician, I can create a KB article with a rich text editor (TipTap), so I can document solutions with formatting, code blocks, and images.

**US2:** As an admin, I can organize articles into categories, so the knowledge base is structured and browsable.

**US3:** As an admin, I can manage article status (draft/published/archived), so only quality-reviewed content is visible to employees.

**US4:** As a technician, I can view the version history of an article, so I can see what changed and when.

**US5:** As an employee, I can browse and search the knowledge base, so I can find solutions without filing a ticket.

**US6:** As an employee, when creating a ticket I see suggested KB articles matching my description, so I can resolve issues without waiting for support.

**US7:** As a technician, I can search articles with full-text search, so I can quickly find relevant documentation.

**US8:** As an admin, I can see article analytics (view count), so I know which articles are most useful.

## Entities & States

### Article

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | ULID | Yes | Primary key |
| company_id | ULID | Yes | Tenant isolation |
| title | String(300) | Yes | Article title |
| slug | String(350) | Yes | URL-friendly slug (unique per company) |
| content | Text | Yes | Rich text content (HTML from TipTap) |
| excerpt | String(500) | No | Short summary for search results |
| category_id | ULID | No | FK to category |
| status | Enum | Yes | draft, published, archived |
| author_id | ULID | Yes | Creator |
| view_count | Integer | Yes | Default 0 |
| search_vector | TSVector | No | PostgreSQL full-text search index |
| published_at | DateTime | No | When first published |
| created_at | DateTime | Yes | Auto-set |
| updated_at | DateTime | Yes | Auto-updated |

### ArticleCategory

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | ULID | Yes | Primary key |
| company_id | ULID | Yes | Tenant isolation |
| name | String(100) | Yes | Category name |
| slug | String(120) | Yes | URL-friendly slug |
| description | String(300) | No | Category description |
| sort_order | Integer | Yes | Display order |
| created_at | DateTime | Yes | Auto-set |

### ArticleVersion

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | ULID | Yes | Primary key |
| article_id | ULID | Yes | FK to article |
| version_number | Integer | Yes | Incrementing version |
| title | String(300) | Yes | Title at this version |
| content | Text | Yes | Content at this version |
| edited_by | ULID | Yes | Who made the edit |
| created_at | DateTime | Yes | Auto-set |

### Article Status State Machine

```
draft → published → archived
  │         │           │
  │         └── draft ──┘  (unpublish/unarchive)
  │
  └── (delete only from draft)
```

Valid transitions:
- draft → published (publish)
- published → draft (unpublish), archived (archive)
- archived → draft (restore)

## Use Cases

**UC1: Create Article**
- Actor: Technician+
- Steps: Fill title + content in TipTap editor → Select category → Save as draft → Auto-generate slug

**UC2: Publish Article**
- Actor: Admin
- Steps: Review draft → Change status to published → Set published_at → Create version snapshot

**UC3: Edit Article**
- Actor: Technician+ (author or admin)
- Steps: Edit content → Save → Create new version entry → Update search vector

**UC4: Search Articles**
- Actor: Any authenticated user
- Steps: Enter search query → Full-text search with ranking → Return ranked results

**UC5: Browse Self-Service KB**
- Actor: Employee
- Steps: Browse categories → View published articles → Increment view count

**UC6: Article Deflection on Ticket Creation**
- Actor: Employee
- Steps: Type ticket description → System suggests matching published articles → Employee can view article or proceed with ticket

## Collateral Impact

| Component | Impact | Action Required |
|-----------|--------|----------------|
| `app.py` | Register KB router | Add include_router |
| `web/app/src/router.tsx` | Add KB routes | New pages |
| `web/app/src/components/layout/Sidebar.tsx` | Add sidebar entries | Under new Knowledge section |
| `web/app/src/locales/` | i18n translations | EN + ES |
| `web/app/src/types/index.ts` | TypeScript interfaces | KB types |
| `web/app/package.json` | TipTap dependencies | Install @tiptap packages |

## API Endpoints

### Article CRUD

| Method | Path | Role | Description |
|--------|------|------|-------------|
| POST | /api/v1/kb/articles | technician+ | Create article (draft) |
| GET | /api/v1/kb/articles | technician+ | List articles (all statuses, paginated) |
| GET | /api/v1/kb/articles/:id | any auth | Get article detail |
| PUT | /api/v1/kb/articles/:id | technician+ | Update article |
| DELETE | /api/v1/kb/articles/:id | admin | Delete article (draft only) |

### Article Actions

| Method | Path | Role | Description |
|--------|------|------|-------------|
| POST | /api/v1/kb/articles/:id/publish | admin | Publish article |
| POST | /api/v1/kb/articles/:id/unpublish | admin | Unpublish to draft |
| POST | /api/v1/kb/articles/:id/archive | admin | Archive article |
| POST | /api/v1/kb/articles/:id/restore | admin | Restore from archive |
| GET | /api/v1/kb/articles/:id/versions | technician+ | Get version history |

### Categories

| Method | Path | Role | Description |
|--------|------|------|-------------|
| POST | /api/v1/kb/categories | admin | Create category |
| GET | /api/v1/kb/categories | any auth | List categories |
| PUT | /api/v1/kb/categories/:id | admin | Update category |
| DELETE | /api/v1/kb/categories/:id | admin | Delete category (if no articles) |

### Search & Self-Service

| Method | Path | Role | Description |
|--------|------|------|-------------|
| GET | /api/v1/kb/search | any auth | Full-text search articles |
| GET | /api/v1/kb/public | employee+ | Browse published articles (self-service) |
| GET | /api/v1/kb/suggest | employee+ | Suggest articles matching a description |

## Definition of Done

- [ ] `kb_bc` bounded context created with domain entities, enums, exceptions
- [ ] Article CRUD endpoints working with pagination and filters
- [ ] TipTap WYSIWYG editor integrated in frontend
- [ ] Article categories CRUD
- [ ] Article status workflow (draft/published/archived)
- [ ] Version history on every edit
- [ ] PostgreSQL full-text search with tsvector
- [ ] Employee self-service browse and search
- [ ] AI-powered article suggestion on ticket creation
- [ ] Frontend: Article list, detail, create/edit with TipTap
- [ ] Frontend: Self-service KB portal for employees
- [ ] Frontend: Sidebar navigation entries
- [ ] i18n: EN + ES translations
- [ ] Unit tests for all command/query handlers
- [ ] Integration tests for all endpoints
- [ ] All tests passing (unit + integration)

## Open Questions

None — scope is well-defined from the roadmap description.

## Resolved Decisions

1. **Separate BC:** Knowledge base is a new `kb_bc` bounded context. Articles are a distinct domain from requests and incidents.
2. **Rich text format:** Store TipTap output as HTML in the database. TipTap outputs clean HTML that can be rendered safely.
3. **Search strategy:** PostgreSQL tsvector for full-text search — no external search engine needed for v1.
4. **AI suggestions:** Use the existing OpenAI integration to match ticket descriptions against KB article content.
5. **Slug generation:** Auto-generate URL-friendly slugs from titles, with collision handling (append -2, -3, etc.).
6. **Version storage:** Full content snapshots per version (not diffs). Simpler to implement and query.
