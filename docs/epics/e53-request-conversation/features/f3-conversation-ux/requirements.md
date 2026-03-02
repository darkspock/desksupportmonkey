# Feature: Conversation UX

**Parent Epic:** [../../requirements.md](../../requirements.md)
**Feature #:** F3
**Dependencies:** F1 (Waiting Status)
**Complexity:** S

## Scope

### Included
- Redesign comment section in `RequestDetailPage.tsx` as conversation bubbles
  - Employee messages: right-aligned, neutral background
  - Technician messages: left-aligned, brand-colored accent
  - Author name, role badge (Employee / Technician), relative timestamp on each message
  - Messages grouped by date ("Today", "Yesterday", "Feb 28")
- "Waiting for your reply" amber banner when request status is `waiting_for_employee`
  - Shown at top of comment section for the employee
  - Comment input visually emphasized (highlight border)
  - Banner disappears after employee submits a reply (status auto-transitions via F1)
- Status change dialog for `waiting_for_employee` with optional message
  - Dialog includes text field: "What do you need from the employee?"
  - If text provided, saved as comment before status change (single API call or sequential)
  - Both comment and status change trigger notifications (via F1 events + F2 emails if deployed)
- i18n keys for banner, dialog placeholder, and conversation UI labels (EN + ES)

### Excluded (in other features)
- `waiting_for_employee` status, transitions, SLA pause, auto-transition → F1
- Email notifications → F2
- Comment edit/delete (intentionally immutable for audit trail)

## User Value

The comment section transforms from a flat log into a visual conversation. Users can immediately see who said what with clear role distinction. Employees viewing a request in "waiting for employee" see a prominent banner telling them the technician needs their response. Technicians can include a message explaining what they need when setting the waiting status.

## Acceptance Criteria

- [ ] Employee messages aligned right with neutral/gray background
- [ ] Technician messages aligned left with brand-colored accent (teal/blue)
- [ ] Each message shows: author name, role badge (Employee / Technician / Admin), relative timestamp
- [ ] Messages grouped by date separator ("Today", "Yesterday", date for older)
- [ ] Amber/warning banner at top of comment section when status is `waiting_for_employee`: "The technician is waiting for your reply"
- [ ] Comment input highlighted when status is `waiting_for_employee` (e.g., accent border)
- [ ] Banner disappears after employee submits reply (status auto-transitions to `in_progress`)
- [ ] Status change dropdown for `waiting_for_employee` opens dialog with optional text field
- [ ] If text provided in dialog, it's saved as a comment (visible in conversation) before the status changes
- [ ] Dialog text field placeholder: "What do you need from the employee?" / "¿Qué necesitas del empleado?"
- [ ] i18n keys added for all new UI text (EN + ES)
- [ ] Existing comment functionality (submit, display) still works correctly
- [ ] `make test` and `make lint` pass

## Technical Scope

### Entities (owned by this feature)
- None (frontend-only feature)

### Entities (used from dependencies)
- `ServiceRequest.status` (from F1) — to check if `waiting_for_employee` for banner display
- `RequestComment` (existing) — displayed as conversation bubbles
- `User` (existing) — author name and role for badge display

### Key Components
- `web/app/src/pages/technician/RequestDetailPage.tsx` — Redesign comment section:
  - New `ConversationBubble` component (or inline) for each comment
  - Date separator between message groups
  - Waiting banner component (conditional on status)
  - Status change dialog with optional message text field
- `web/app/src/locales/en.ts` — Add i18n keys for banner, dialog, role badges
- `web/app/src/locales/es.ts` — Add i18n keys for banner, dialog, role badges

## Notes

- The comment API already returns `author_id` and `author_email`. To display role badges (Employee vs Technician), the frontend needs to know the author's role. Options:
  1. The comments API already returns user info — check if role is included
  2. If not, add `author_role` to the comment response DTO (minor backend change, owned by this feature)
- The "status change with optional message" dialog needs to either: (A) make two sequential API calls (POST comment + PATCH status), or (B) extend the status change endpoint to accept an optional `comment` body. Option A is simpler and avoids backend changes; Option B is cleaner but crosses into F1 scope. Recommend Option A for simplicity.
- The conversation bubble layout should work well on mobile — use responsive widths (max 80% of container).
