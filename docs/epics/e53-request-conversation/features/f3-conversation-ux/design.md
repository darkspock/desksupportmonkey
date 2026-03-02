# Solution Design: F3 — Conversation UX

**Requirement:** [requirements.md](requirements.md)
**Date:** 2026-03-02
**Bounded Context:** Frontend (web/app) + minor backend enrichment in request_bc HTTP layer

## Summary

Transform the flat comment list in `RequestDetailPage.tsx` into a chat-bubble conversation layout. Employee messages appear right-aligned with neutral styling; technician/admin messages appear left-aligned with brand accent. Add date separators between message groups, a "waiting for your reply" amber banner when the request is in `waiting_for_employee` status, and a dialog that lets technicians include an optional message when setting the waiting status.

The only backend change is enriching the `CommentResponse` schema with `author_name` and `author_role` fields — the `list_comments` endpoint already resolves users via `find_by_ids`, so adding these two fields is trivial.

## Architecture Decision

**Frontend-first with minimal backend enrichment.** The requirement is labeled S complexity and is "frontend-only", but the comment API currently returns only `author_email` — no role or name. Without `author_role`, the frontend cannot reliably display role badges (comparing `author_id === request.created_by` fails for admin comments or multi-technician scenarios). Adding `author_role` and `author_name` to the response is a 5-line change in an already-existing query — far simpler than building a secondary user-lookup cache on the frontend.

**Alternatives considered:**
- *Pure frontend inference*: Derive role from `author_id === created_by` → "Employee", else "Technician". Rejected: inaccurate for admins and multi-technician teams.
- *Separate user lookup API call*: Frontend fetches `/users/{id}` for each unique author. Rejected: N+1 requests, unnecessary complexity.

**Status dialog approach:** Option A from the requirements — two sequential API calls (POST comment + PATCH status). No backend changes to the status endpoint. This avoids crossing into F1 scope and keeps the backend surface minimal.

## Existing Code Analysis

| Component | Location | Reusable | Modifications Needed |
|-----------|----------|----------|---------------------|
| `RequestDetailPage.tsx` | `web/app/src/pages/technician/RequestDetailPage.tsx` | Yes | Replace comment rendering (lines 932-987) with conversation bubbles; add waiting banner; intercept `waiting_for_employee` status change with dialog |
| Comment rendering | Inline in RequestDetailPage (lines 932-987) | Rewrite | Transform flat list → chat bubble layout with date separators |
| `CommentResponse` schema | `adapters/http/api/requests/schemas.py` | Yes | Add `author_name` and `author_role` optional fields |
| `list_comments` endpoint | `adapters/http/api/requests/routers.py` (line 1088) | Yes | Populate `author_name`/`author_role` from existing `_user_maps` data |
| `_build_comment_response` | `adapters/http/api/requests/routers.py` (line 294) | Yes | Add `author_name`/`author_role` parameters |
| `Comment` TypeScript type | `web/app/src/types/index.ts` (line 207) | Yes | Add `author_name` and `author_role` fields |
| `formatDateTime` | `web/app/src/lib/date.ts` | Yes | Add sibling `formatRelativeDate()` for date separators |
| i18n files | `web/app/src/locales/{en,es}.ts` | Yes | Add ~15 new keys for banner, dialog, badges |
| Inline modal pattern | RequestDetailPage (Reject/Reopen dialogs) | Reuse | Same pattern for "Waiting for employee" dialog |
| `ConfirmDialog` component | `web/app/src/components/ui/ConfirmDialog.tsx` | No | Not suitable — we need a textarea in the dialog, not just confirm/cancel |
| `_user_maps` helper | `adapters/http/api/requests/routers.py` (line 188) | Yes | Already fetches full User objects with role — just need to expose it |

## Implementation Plan

### 1. Backend — Comment Response Enrichment

#### Schema Change

**File:** `adapters/http/api/requests/schemas.py`

Add two optional fields to `CommentResponse`:

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

#### Router Changes

**File:** `adapters/http/api/requests/routers.py`

**`list_comments` endpoint (line 1088):** Change from `_user_email_map` to `_user_maps` to also get names, and add a role map:

```python
def list_comments(...):
    ...
    users = user_repo.find_by_ids([c.author_id for c in comments])
    return {
        "data": [
            CommentResponse(
                id=c.id, request_id=c.request_id, author_id=c.author_id,
                author_email=users.get(c.author_id, None) and users[c.author_id].email,
                author_name=_display_name(users[c.author_id]) if c.author_id in users else None,
                author_role=users[c.author_id].role.value if c.author_id in users else None,
                body=c.body, created_at=c.created_at,
            ).model_dump(mode="json")
            for c in comments
        ]
    }
```

**`_build_comment_response` helper (line 294):** Add `author_name` and `author_role` parameters:

```python
def _build_comment_response(
    comment_id: str, request_id: str, author_id: str,
    author_email: str, author_name: str | None, author_role: str,
    body: str,
) -> dict:
    return CommentResponse(
        id=comment_id, request_id=request_id, author_id=author_id,
        author_email=author_email, author_name=author_name,
        author_role=author_role,
        body=body.strip(),
        created_at=datetime.now(timezone.utc),
    ).model_dump(mode="json")
```

**`add_comment` endpoint (line 1048):** Pass `current_user.name` and `current_user.role.value`:

```python
return {"data": _build_comment_response(
    comment_id, request_id, current_user.id,
    current_user.email,
    current_user.name,
    current_user.role.value,
    body.body,
)}
```

**`add_note` and `list_notes` endpoints:** Apply the same enrichment pattern for consistency (add `author_name` and `author_role` to `NoteResponse`). This keeps both response shapes aligned.

### 2. Frontend — TypeScript Types

**File:** `web/app/src/types/index.ts`

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
```

Same for `Note` interface.

### 3. Frontend — Date Utility

**File:** `web/app/src/lib/date.ts`

Add `formatRelativeDate()` for date separators:

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

  // Format as "Mar 2" or localized equivalent
  return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
}
```

### 4. Frontend — Conversation Bubbles

**File:** `web/app/src/pages/technician/RequestDetailPage.tsx`

Replace the current flat comment rendering (lines 932-987) with a conversation layout.

#### Bubble Layout

```tsx
{/* Conversation bubbles */}
{comments?.length ? (
  <div className="space-y-3">
    {comments.map((c, idx) => {
      const isEmployee = c.author_role === 'employee';
      const displayName = c.author_name || c.author_email?.split('@')[0] || c.author_id;
      const initials = (displayName).split(/[\s.]/).map(p => p[0]?.toUpperCase() ?? '').join('').slice(0, 2);

      // Date separator
      const prevDate = idx > 0 ? comments[idx - 1].created_at?.split('T')[0] : null;
      const currDate = c.created_at?.split('T')[0];
      const showDateSep = currDate !== prevDate;

      const roleBadge = isEmployee
        ? t('page.request_detail.role_employee')
        : t('page.request_detail.role_technician');

      return (
        <div key={c.id}>
          {showDateSep && (
            <div className="flex items-center gap-3 py-2">
              <div className="h-px flex-1 bg-border" />
              <span className="text-xs text-muted-foreground font-medium">
                {formatRelativeDate(c.created_at, t)}
              </span>
              <div className="h-px flex-1 bg-border" />
            </div>
          )}
          <div className={`flex gap-3 ${isEmployee ? 'flex-row-reverse' : ''}`}>
            {/* Avatar */}
            <div className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full ${
              isEmployee ? 'bg-muted' : 'bg-primary/10'
            }`}>
              <span className={`text-xs font-medium ${
                isEmployee ? 'text-muted-foreground' : 'text-primary'
              }`}>{initials}</span>
            </div>
            {/* Bubble */}
            <div className={`max-w-[80%] space-y-1 ${isEmployee ? 'items-end' : ''}`}>
              <div className={`flex items-baseline gap-2 ${isEmployee ? 'flex-row-reverse' : ''}`}>
                <span className="text-sm font-medium text-foreground">{displayName}</span>
                <span className={`inline-flex items-center rounded px-1.5 py-0.5 text-[10px] font-medium ${
                  isEmployee
                    ? 'bg-muted text-muted-foreground'
                    : 'bg-primary/10 text-primary'
                }`}>{roleBadge}</span>
                <span className="text-xs text-muted-foreground">{formatDateTime(c.created_at)}</span>
              </div>
              <div className={`rounded-lg p-3 ${
                isEmployee
                  ? 'bg-muted/50 border border-border'
                  : 'bg-primary/5 border border-primary/20'
              }`}>
                <p className="text-sm text-foreground leading-relaxed whitespace-pre-wrap">{c.body}</p>
              </div>
            </div>
          </div>
        </div>
      );
    })}
  </div>
) : (
  <p className="text-sm text-muted-foreground">{t('page.request_detail.no_comments')}</p>
)}
```

**Key design choices:**
- Employee messages: `flex-row-reverse` → right-aligned, `bg-muted/50` neutral background
- Technician messages: normal flex → left-aligned, `bg-primary/5` brand-colored accent
- Role badge: small pill next to author name ("Employee" / "Technician")
- Max width `80%` for mobile responsiveness
- Date separator: horizontal line with centered label ("Today", "Yesterday", "Mar 2")

### 5. Frontend — Waiting Banner

**File:** `web/app/src/pages/technician/RequestDetailPage.tsx`

Add an amber banner at the top of the comments section when `request.status === 'waiting_for_employee'`:

```tsx
{request.status === 'waiting_for_employee' && (
  <div className="flex items-center gap-3 rounded-lg border border-amber-200 bg-amber-50 p-3 dark:border-amber-900 dark:bg-amber-950/50">
    <svg className="h-5 w-5 text-amber-600 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <circle cx="12" cy="12" r="10" /><path d="M12 6v6l4 2" />
    </svg>
    <p className="text-sm font-medium text-amber-800 dark:text-amber-200">
      {isTech
        ? t('page.request_detail.waiting_banner_tech')
        : t('page.request_detail.waiting_banner_employee')}
    </p>
  </div>
)}
```

**Comment input highlight:** When `waiting_for_employee`, add accent border to the textarea:

```tsx
<textarea
  ...
  className={`w-full resize-none ${
    request.status === 'waiting_for_employee' && !isTech
      ? 'ring-2 ring-amber-400 border-amber-400'
      : ''
  }`}
/>
```

### 6. Frontend — Waiting Status Dialog

**File:** `web/app/src/pages/technician/RequestDetailPage.tsx`

Add state:
```tsx
const [showWaitingDialog, setShowWaitingDialog] = useState(false);
const [waitingMessage, setWaitingMessage] = useState('');
```

Intercept `waiting_for_employee` status change. Modify the `onStatusClick` and status button logic. Wherever `changeStatus.mutate({ status: 'waiting_for_employee' })` would fire, instead call `setShowWaitingDialog(true)`.

**Interception points:**
1. **`StatusProgressTracker` `onStatusClick` callback (line 787):** Wrap in a function that checks if target status is `waiting_for_employee`:
```tsx
onStatusClick={isTech ? (status) => {
  if (status === 'waiting_for_employee') {
    setShowWaitingDialog(true);
  } else {
    changeStatus.mutate({ status });
  }
} : undefined}
```

2. **Right column primary action button (line 1064):** Same interception:
```tsx
onClick={() => {
  if (reopenTarget) {
    setShowReopenForm(true);
  } else if (primaryNext === 'waiting_for_employee') {
    setShowWaitingDialog(true);
  } else {
    changeStatus.mutate({ status: primaryNext });
  }
}}
```

**Dialog (inline modal, following existing Reject/Reopen pattern):**

```tsx
{showWaitingDialog && (
  <div className="fixed inset-0 z-50 flex items-center justify-center">
    <div className="fixed inset-0 bg-black/50" onClick={() => { setShowWaitingDialog(false); setWaitingMessage(''); }} />
    <div className="relative z-10 w-full max-w-md rounded-lg border border-border bg-card p-6 shadow-lg space-y-4">
      <h3 className="text-lg font-semibold text-foreground">
        {t('page.request_detail.waiting_dialog_title')}
      </h3>
      <p className="text-sm text-muted-foreground">
        {t('page.request_detail.waiting_dialog_description')}
      </p>
      <textarea
        value={waitingMessage}
        onChange={(e) => setWaitingMessage(e.target.value)}
        placeholder={t('page.request_detail.waiting_dialog_placeholder')}
        rows={3}
        className="w-full resize-none rounded-md border border-border bg-background px-3 py-2 text-sm"
      />
      <div className="flex justify-end gap-2">
        <button
          onClick={() => { setShowWaitingDialog(false); setWaitingMessage(''); }}
          className="inline-flex items-center justify-center rounded-md h-9 px-4 text-sm font-medium border border-border bg-background hover:bg-accent transition-colors"
        >
          {t('action.cancel')}
        </button>
        <button
          onClick={async () => {
            if (waitingMessage.trim()) {
              await api.post(`/requests/${id}/comments`, { body: waitingMessage.trim() });
              queryClient.invalidateQueries({ queryKey: ['request-comments', id] });
            }
            changeStatus.mutate({ status: 'waiting_for_employee' });
            setShowWaitingDialog(false);
            setWaitingMessage('');
          }}
          disabled={changeStatus.isPending}
          className="inline-flex items-center justify-center rounded-md h-9 px-4 text-sm font-medium bg-amber-500 text-white hover:bg-amber-600 transition-colors disabled:opacity-50"
        >
          {t('page.request_detail.waiting_dialog_confirm')}
        </button>
      </div>
    </div>
  </div>
)}
```

**Key design choices:**
- Dialog uses the established inline modal pattern (same as Reject/Reopen)
- Text field is optional — technician can submit without a message
- If message provided: POST comment first, then PATCH status (Option A from requirements)
- Confirm button is amber (matching the waiting status color)
- On success: comment list + request data are invalidated to refresh

### 7. Frontend — i18n Keys

**File:** `web/app/src/locales/en.ts`

```typescript
// Conversation UX
'page.request_detail.role_employee': 'Employee',
'page.request_detail.role_technician': 'Technician',
'page.request_detail.role_admin': 'Admin',

// Waiting banner
'page.request_detail.waiting_banner_employee': 'The technician is waiting for your reply',
'page.request_detail.waiting_banner_tech': 'Waiting for the employee to reply',

// Waiting dialog
'page.request_detail.waiting_dialog_title': 'Set as waiting for employee',
'page.request_detail.waiting_dialog_description': 'The employee will be notified that you need their response.',
'page.request_detail.waiting_dialog_placeholder': 'What do you need from the employee?',
'page.request_detail.waiting_dialog_confirm': 'Set as waiting',

// Date separators
'date.today': 'Today',
'date.yesterday': 'Yesterday',
```

**File:** `web/app/src/locales/es.ts`

```typescript
// Conversation UX
'page.request_detail.role_employee': 'Empleado',
'page.request_detail.role_technician': 'Técnico',
'page.request_detail.role_admin': 'Admin',

// Waiting banner
'page.request_detail.waiting_banner_employee': 'El técnico está esperando tu respuesta',
'page.request_detail.waiting_banner_tech': 'Esperando la respuesta del empleado',

// Waiting dialog
'page.request_detail.waiting_dialog_title': 'Marcar como pendiente del empleado',
'page.request_detail.waiting_dialog_description': 'Se notificará al empleado que necesitas su respuesta.',
'page.request_detail.waiting_dialog_placeholder': '¿Qué necesitas del empleado?',
'page.request_detail.waiting_dialog_confirm': 'Marcar como pendiente',

// Date separators
'date.today': 'Hoy',
'date.yesterday': 'Ayer',
```

## Collateral Changes

### Files to Modify

| File | Change Type | Description |
|------|-------------|-------------|
| `adapters/http/api/requests/schemas.py` | Modify | Add `author_name`, `author_role` to `CommentResponse` (and `NoteResponse`) |
| `adapters/http/api/requests/routers.py` | Modify | Populate new fields in `list_comments`, `add_comment`, `list_notes`, `add_note`, `_build_comment_response`, `_build_note_response` |
| `web/app/src/types/index.ts` | Modify | Add `author_name`, `author_role` to `Comment` and `Note` interfaces |
| `web/app/src/lib/date.ts` | Modify | Add `formatRelativeDate()` function |
| `web/app/src/pages/technician/RequestDetailPage.tsx` | Modify | Conversation bubbles, waiting banner, waiting dialog, status interception |
| `web/app/src/locales/en.ts` | Modify | Add ~12 i18n keys |
| `web/app/src/locales/es.ts` | Modify | Add ~12 i18n keys |

### Breaking Changes

| Change | Impact | Migration |
|--------|--------|-----------|
| `CommentResponse` adds new optional fields | None — additive | Backward compatible: old clients ignore new fields |
| `NoteResponse` adds new optional fields | None — additive | Backward compatible |

## Testing Strategy

| Test Type | Scope | Priority |
|-----------|-------|----------|
| Integration | `list_comments` returns `author_name` and `author_role` | High |
| Integration | `add_comment` returns `author_name` and `author_role` | High |
| Integration | `list_notes` returns `author_name` and `author_role` | Medium |
| Manual | Conversation bubbles render correctly (employee right, tech left) | High |
| Manual | Date separators show "Today", "Yesterday", date | Medium |
| Manual | Waiting banner appears for `waiting_for_employee` status | High |
| Manual | Waiting dialog opens, optional comment posted, status changes | High |
| Manual | Banner disappears after employee replies (auto-transition) | High |
| Manual | Mobile responsive — bubbles max 80% width | Medium |

**Integration test additions** (`tests/integration/test_requests_endpoints.py`):

```python
class TestCommentResponseEnrichment:
    def test_list_comments_includes_author_name_and_role(self, ...):
        """GET comments returns author_name and author_role."""
        # Create request, add comment, list comments
        # Assert response includes author_name and author_role fields

    def test_add_comment_returns_author_name_and_role(self, ...):
        """POST comment returns author_name and author_role of current user."""
        # Add comment, verify response fields
```

## Implementation Order

1. [ ] Backend: Add `author_name` and `author_role` to `CommentResponse` and `NoteResponse` schemas
2. [ ] Backend: Update `list_comments`, `add_comment`, `list_notes`, `add_note` and helper functions
3. [ ] Backend: Integration tests for enriched response
4. [ ] Frontend: Update `Comment` and `Note` TypeScript types
5. [ ] Frontend: Add `formatRelativeDate()` to `date.ts`
6. [ ] Frontend: Add i18n keys (EN + ES)
7. [ ] Frontend: Conversation bubbles + date separators (replace comment rendering)
8. [ ] Frontend: Waiting banner
9. [ ] Frontend: Waiting dialog + status interception
10. [ ] Verification: `make test`, `make lint`, manual visual check

## Open Technical Questions

None — all decisions resolved in the design.

## Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Role badge shows "Admin" for admin comments — may confuse employees | Low | Low | Use "Technician" label for all non-employee roles (admin, super_admin, procurement_manager) — employees don't need to distinguish admin vs technician |
| Sequential API calls in waiting dialog (POST comment + PATCH status) could partially fail | Low | Medium | If comment succeeds but status change fails, the comment is still valuable context. Toast error for the status failure. No rollback needed. |
| Large conversation threads (100+ comments) may render slowly | Very Low | Low | No pagination designed — revisit if real usage shows performance issues. Comments are lightweight text. |
