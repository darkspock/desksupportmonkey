# Implementation Tasks: F3 — Conversation UX

**Requirement:** [requirements.md](requirements.md)
**Solution Design:** [design.md](design.md)
**Created:** 2026-03-02
**Total Tasks:** 10
**Estimated Complexity:** S

## Summary

| Phase | Tasks | Complexity |
|-------|-------|------------|
| HTTP — Backend Schema Enrichment | 1 | S |
| HTTP — Backend Router Enrichment | 1 | S |
| Tests — Backend Integration | 1 | S |
| Frontend — TypeScript Types | 1 | S |
| Frontend — Date Utility | 1 | S |
| Frontend — i18n Keys | 1 | S |
| Frontend — Conversation Bubbles | 1 | M |
| Frontend — Waiting Banner | 1 | S |
| Frontend — Waiting Dialog | 1 | M |
| Verification | 1 | S |

---

## Phase 1: HTTP — Backend Schema Enrichment

### TASK-001: Add `author_name` and `author_role` to `CommentResponse` and `NoteResponse`

**Phase:** HTTP — Schema
**Complexity:** S
**Dependencies:** None

**Description:**
Add two new optional fields to `CommentResponse` and `NoteResponse` Pydantic schemas so the frontend can display author names and role badges.

**File:** `adapters/http/api/requests/schemas.py`

**Implementation:**
```python
class CommentResponse(BaseModel):
    id: str
    request_id: str
    author_id: str
    author_email: Optional[str] = None
    author_name: Optional[str] = None   # NEW
    author_role: Optional[str] = None   # NEW
    body: str
    created_at: Optional[datetime] = None
```

Apply the same two fields to `NoteResponse`.

**Acceptance Criteria:**
- [x] `CommentResponse` has `author_name: Optional[str] = None`
- [x] `CommentResponse` has `author_role: Optional[str] = None`
- [x] `NoteResponse` has the same two new fields
- [x] Both fields are optional — backward compatible

---

## Phase 2: HTTP — Backend Router Enrichment

### TASK-002: Populate `author_name` and `author_role` in comment/note endpoints

**Phase:** HTTP — Router
**Complexity:** S
**Dependencies:** TASK-001

**Description:**
Update four endpoints and two helper functions to populate the new `author_name` and `author_role` fields. The `_user_maps` / `find_by_ids` already fetch full User objects with `role` and `name` — just expose them.

**File:** `adapters/http/api/requests/routers.py`

**Changes:**

1. **`list_comments` (line ~1088):** Replace `_user_email_map` with direct `user_repo.find_by_ids()` call. Build the `CommentResponse` with `author_name=_display_name(user)` and `author_role=user.role.value`.

2. **`_build_comment_response` (line ~294):** Add `author_name: str | None` and `author_role: str` parameters. Pass them to `CommentResponse(...)`.

3. **`add_comment` (line ~1048):** Pass `current_user.name` and `current_user.role.value` to `_build_comment_response`.

4. **`list_notes` (line ~1145):** Same pattern as `list_comments` — use `find_by_ids` and populate `author_name`/`author_role`.

5. **`_build_note_response` (line ~307):** Add `author_name` and `author_role` parameters.

6. **`add_note` (line ~1115):** Pass `current_user.name` and `current_user.role.value` to `_build_note_response`.

**Acceptance Criteria:**
- [x] `GET /requests/{id}/comments` returns `author_name` and `author_role` for each comment
- [x] `POST /requests/{id}/comments` response includes `author_name` and `author_role`
- [x] `GET /requests/{id}/notes` returns `author_name` and `author_role` for each note
- [x] `POST /requests/{id}/notes` response includes `author_name` and `author_role`
- [x] Existing tests still pass (additive change)

---

## Phase 3: Tests — Backend Integration

### TASK-003: Integration tests for comment/note response enrichment

**Phase:** Tests
**Complexity:** S
**Dependencies:** TASK-002

**Description:**
Add integration tests verifying the new `author_name` and `author_role` fields are returned by the comment and note endpoints.

**File:** `tests/integration/test_requests_endpoints.py` (EXTEND)

**Test Cases:**

```python
class TestCommentResponseEnrichment:
    def test_list_comments_includes_author_name_and_role(self, client, auth_as, employee_user):
        """GET comments returns author_name and author_role."""
        auth_as(employee_user)
        create_resp = _create_request(client, title="Enrichment test")
        req_id = create_resp.json()["data"]["id"]
        client.post(f"/api/v1/requests/{req_id}/comments", json={"body": "Test"})

        resp = client.get(f"/api/v1/requests/{req_id}/comments")
        assert resp.status_code == 200
        comment = resp.json()["data"][0]
        assert "author_name" in comment
        assert comment["author_role"] == "employee"

    def test_add_comment_returns_author_name_and_role(self, client, auth_as, employee_user):
        """POST comment returns author_name and author_role of current user."""
        auth_as(employee_user)
        create_resp = _create_request(client, title="Enrichment test")
        req_id = create_resp.json()["data"]["id"]

        resp = client.post(f"/api/v1/requests/{req_id}/comments", json={"body": "Test"})
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["author_role"] == "employee"
        assert "author_name" in data
```

**Acceptance Criteria:**
- [x] `test_list_comments_includes_author_name_and_role` passes
- [x] `test_add_comment_returns_author_name_and_role` passes
- [x] All existing comment/note tests still pass

---

## Phase 4: Frontend — TypeScript Types

### TASK-004: Add `author_name` and `author_role` to `Comment` and `Note` interfaces

**Phase:** Frontend — Types
**Complexity:** S
**Dependencies:** TASK-001

**Description:**
Update the TypeScript interfaces to include the new fields from the enriched API response.

**File:** `web/app/src/types/index.ts`

**Implementation:**
```typescript
export interface Comment {
  id: string;
  request_id: string;
  author_id: string;
  author_email?: string | null;
  author_name?: string | null;   // NEW
  author_role?: string | null;   // NEW
  body: string;
  created_at: string;
}

export interface Note {
  id: string;
  request_id: string;
  author_id: string;
  author_email?: string | null;
  author_name?: string | null;   // NEW
  author_role?: string | null;   // NEW
  body: string;
  created_at: string;
}
```

**Acceptance Criteria:**
- [x] `Comment` interface has `author_name?: string | null`
- [x] `Comment` interface has `author_role?: string | null`
- [x] `Note` interface has the same two new fields
- [x] `npm run build` passes (no type errors)

---

## Phase 5: Frontend — Date Utility

### TASK-005: Add `formatRelativeDate()` to date utilities

**Phase:** Frontend — Utility
**Complexity:** S
**Dependencies:** None

**Description:**
Add a function for date separators in the conversation view. Returns "Today", "Yesterday", or a short formatted date (e.g., "Mar 2").

**File:** `web/app/src/lib/date.ts`

**Implementation:**
```typescript
export function formatRelativeDate(
  value: string | Date | null | undefined,
  t: (key: string) => string,
): string {
  if (!value) return '';
  const date = parseDate(value);
  if (!date) return '';

  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const target = new Date(date.getFullYear(), date.getMonth(), date.getDate());
  const diffDays = Math.floor((today.getTime() - target.getTime()) / 86400000);

  if (diffDays === 0) return t('date.today');
  if (diffDays === 1) return t('date.yesterday');

  return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
}
```

**Acceptance Criteria:**
- [x] Returns `t('date.today')` for today's date
- [x] Returns `t('date.yesterday')` for yesterday's date
- [x] Returns localized short date for older dates
- [x] Handles null/undefined gracefully

---

## Phase 6: Frontend — i18n Keys

### TASK-006: Add i18n keys for conversation UX (EN + ES)

**Phase:** Frontend — i18n
**Complexity:** S
**Dependencies:** None

**Description:**
Add translation keys for role badges, waiting banner, waiting dialog, and date separators.

**Files:** `web/app/src/locales/en.ts`, `web/app/src/locales/es.ts`

**EN keys:**
```typescript
'page.request_detail.role_employee': 'Employee',
'page.request_detail.role_technician': 'Technician',
'page.request_detail.role_admin': 'Admin',
'page.request_detail.waiting_banner_employee': 'The technician is waiting for your reply',
'page.request_detail.waiting_banner_tech': 'Waiting for the employee to reply',
'page.request_detail.waiting_dialog_title': 'Set as waiting for employee',
'page.request_detail.waiting_dialog_description': 'The employee will be notified that you need their response.',
'page.request_detail.waiting_dialog_placeholder': 'What do you need from the employee?',
'page.request_detail.waiting_dialog_confirm': 'Set as waiting',
'date.today': 'Today',
'date.yesterday': 'Yesterday',
```

**ES keys:**
```typescript
'page.request_detail.role_employee': 'Empleado',
'page.request_detail.role_technician': 'Técnico',
'page.request_detail.role_admin': 'Admin',
'page.request_detail.waiting_banner_employee': 'El técnico está esperando tu respuesta',
'page.request_detail.waiting_banner_tech': 'Esperando la respuesta del empleado',
'page.request_detail.waiting_dialog_title': 'Marcar como pendiente del empleado',
'page.request_detail.waiting_dialog_description': 'Se notificará al empleado que necesitas su respuesta.',
'page.request_detail.waiting_dialog_placeholder': '¿Qué necesitas del empleado?',
'page.request_detail.waiting_dialog_confirm': 'Marcar como pendiente',
'date.today': 'Hoy',
'date.yesterday': 'Ayer',
```

**Acceptance Criteria:**
- [x] All 11 keys added to `en.ts`
- [x] All 11 keys added to `es.ts`
- [x] No duplicate keys

---

## Phase 7: Frontend — Conversation Bubbles

### TASK-007: Replace flat comment list with conversation bubbles and date separators

**Phase:** Frontend — UI
**Complexity:** M
**Dependencies:** TASK-004, TASK-005, TASK-006

**Description:**
Replace the current flat comment rendering in `RequestDetailPage.tsx` (lines ~932-987) with a chat-bubble conversation layout. Employee messages appear right-aligned with neutral background; technician/admin messages appear left-aligned with brand accent.

**File:** `web/app/src/pages/technician/RequestDetailPage.tsx`

**Implementation (from design):**
- Import `formatRelativeDate` from `../../lib/date`
- For each comment:
  - Determine alignment: `c.author_role === 'employee'` → right-aligned (`flex-row-reverse`), else → left-aligned
  - Display name: `c.author_name || c.author_email?.split('@')[0] || c.author_id`
  - Initials: first letters of display name parts
  - Role badge: "Employee" (neutral pill) or "Technician" (brand pill)
  - Avatar: `bg-muted` for employee, `bg-primary/10` for technician
  - Bubble: `bg-muted/50 border-border` for employee, `bg-primary/5 border-primary/20` for technician
  - Max width `80%` for mobile
- Date separators between messages from different dates:
  - Horizontal line with centered label
  - Compare `created_at` date portion between consecutive messages

**Acceptance Criteria:**
- [x] Employee messages aligned right with neutral/gray background
- [x] Technician messages aligned left with brand-colored accent
- [x] Each message shows: author name, role badge, relative timestamp
- [x] Messages grouped by date separator ("Today", "Yesterday", date)
- [x] Max width 80% for mobile responsiveness
- [x] Existing comment submit functionality still works

---

## Phase 8: Frontend — Waiting Banner

### TASK-008: Add waiting banner and input highlight

**Phase:** Frontend — UI
**Complexity:** S
**Dependencies:** TASK-006

**Description:**
Add an amber banner at the top of the comments section when `request.status === 'waiting_for_employee'`. Show different text for employee vs technician. Highlight the comment input textarea with an amber ring for employees.

**File:** `web/app/src/pages/technician/RequestDetailPage.tsx`

**Implementation (from design):**
- Amber banner with clock icon, `border-amber-200 bg-amber-50` (dark mode: `border-amber-900 bg-amber-950/50`)
- Text: `isTech ? t('waiting_banner_tech') : t('waiting_banner_employee')`
- Textarea highlight for employees: `ring-2 ring-amber-400 border-amber-400` when status is `waiting_for_employee` and `!isTech`

**Acceptance Criteria:**
- [x] Amber banner visible when status is `waiting_for_employee`
- [x] Employee sees "The technician is waiting for your reply"
- [x] Technician sees "Waiting for the employee to reply"
- [x] Comment input has amber ring when employee views `waiting_for_employee` request
- [x] Banner disappears after employee submits reply (auto-transition to `in_progress`)

---

## Phase 9: Frontend — Waiting Dialog

### TASK-009: Add waiting status dialog with optional message

**Phase:** Frontend — UI
**Complexity:** M
**Dependencies:** TASK-006

**Description:**
Intercept the `waiting_for_employee` status change to show a dialog with an optional textarea. If the technician enters a message, POST it as a comment before changing the status (two sequential API calls).

**File:** `web/app/src/pages/technician/RequestDetailPage.tsx`

**Implementation (from design):**

1. **New state:**
```tsx
const [showWaitingDialog, setShowWaitingDialog] = useState(false);
const [waitingMessage, setWaitingMessage] = useState('');
```

2. **Interception points:**
   - `StatusProgressTracker` `onStatusClick` callback (line ~787): check if target is `waiting_for_employee` → open dialog instead
   - Right column primary action button (line ~1064): same interception

3. **Dialog:** Inline modal following existing Reject/Reopen pattern:
   - Title: `t('waiting_dialog_title')`
   - Description: `t('waiting_dialog_description')`
   - Optional textarea with placeholder: `t('waiting_dialog_placeholder')`
   - Cancel button + amber Confirm button
   - On confirm: if message provided, `await api.post(comments)` then `changeStatus.mutate`; if no message, just `changeStatus.mutate`
   - Invalidate `['request-comments', id]` after posting comment

**Acceptance Criteria:**
- [x] Clicking `waiting_for_employee` opens dialog instead of immediately changing status
- [x] Dialog has optional textarea with placeholder
- [x] If text provided, comment is posted before status change
- [x] If no text, status changes directly
- [x] Dialog uses amber confirm button
- [x] Dialog follows existing inline modal pattern (Reject/Reopen)
- [x] Both interception points work (status tracker + sidebar button)

---

## Phase 10: Verification

### TASK-010: Run full test suite and verify

**Phase:** Verification
**Complexity:** S
**Dependencies:** TASK-003, TASK-007, TASK-008, TASK-009

**Description:**
Run `make test` and frontend build to ensure no regressions. Verify all acceptance criteria from the requirements.

**Acceptance Criteria:**
- [x] `make test` passes (no new failures)
- [x] `npm run build` passes in `web/app/` (no TypeScript errors)
- [x] All 13 acceptance criteria from requirements.md verified
- [x] Both EN and ES translations render correctly

---

## Dependency Graph

```
TASK-001 (schema) ── TASK-002 (router) ── TASK-003 (integration tests)
     │
     └── TASK-004 (TS types) ──┐
                                │
TASK-005 (date util) ──────────┤
                                ├── TASK-007 (conversation bubbles)
TASK-006 (i18n) ───────────────┤
                                ├── TASK-008 (waiting banner)
                                │
                                └── TASK-009 (waiting dialog)
                                            │
                                     TASK-010 (verification)
```

## Execution Order

**Batch 1 (Parallel — no dependencies):** TASK-001, TASK-005, TASK-006
**Batch 2 (Sequential):** TASK-002 (depends on TASK-001)
**Batch 3 (Parallel):** TASK-003 (depends on TASK-002), TASK-004 (depends on TASK-001)
**Batch 4 (Parallel):** TASK-007 (depends on TASK-004, TASK-005, TASK-006), TASK-008 (depends on TASK-006), TASK-009 (depends on TASK-006)
**Batch 5:** TASK-010 (depends on all)

## Final Checklist

- [x] All 10 tasks completed
- [x] All backend integration tests passing
- [x] `make test` passes
- [x] `npm run build` passes
- [x] Employee messages right-aligned, neutral background
- [x] Technician messages left-aligned, brand accent
- [x] Date separators working
- [x] Waiting banner appears/disappears correctly
- [x] Waiting dialog posts comment + changes status
- [x] i18n keys present in EN + ES
