# Screen Design Guide

Practical guide to design and implement product screens with consistent UX across Metrica.uno, based on real issues found in Client Area and Client Portal workflows.

---

## Purpose

Use this guide when creating or reworking screens so users can:
- Understand the page in under 5 seconds
- Complete the main action without guessing
- Recover from errors without getting stuck

This guide complements:
- `ai_docs/architecture/frontend/CODING_STANDARDS.md`
- `ai_docs/architecture/frontend/COMPONENT_LIBRARY.md`

---

## Core Principles

1. One screen, one primary goal  
Every page must have one obvious main action.

2. One place to do each action  
Avoid duplicate edit paths for the same data.

3. View-first, edit-second  
Default to read mode; edit in controlled flow (modal or dedicated page).

4. Progressive disclosure  
Show only fields/actions relevant to the selected mode.

5. Clear system feedback  
Users must always know: loading, success, validation issue, or failure.

6. Business language over technical language  
Hide internal technical fields unless they provide real user value.

---

## Standard Screen Structure

1. Header
- Page title
- Short context sentence
- One primary CTA

2. Content sections
- Group by user intent (not by backend model)
- Use clear section titles and helper text

3. Action area
- Primary action fixed and predictable
- Secondary actions visually lower priority

4. States
- Loading state
- Empty state with CTA
- Error state with recovery action

---

## Lists: Tables Over Panels

Default rule for lists of entities: use `tables`, not panel/card grids.

Use tables when users need to:
- Scan many items quickly
- Compare values across rows
- Sort/filter/search
- Perform row actions (view/edit/delete)

Minimum table setup:
- Stable columns with clear labels
- Primary identifier in first column
- Status/date columns where relevant
- Right-aligned actions column
- Empty state with primary CTA

Do not use panel/card layouts for operational lists (clients, users, contracts, reports, notifications).

Allowed exceptions:
- Very small curated sets (e.g., max 3 summary cards)
- Dashboard KPIs (metrics, not entity lists)
- Mobile fallback where table is unreadable (use compact row list, not decorative cards)

---

## Editing Pattern (Default Standard)

Use this pattern unless there is a strong reason not to:

1. Page opens in `View` mode
2. User clicks `Edit`
3. Edit modal opens with focused fields
4. User clicks `Save`
5. Data refreshes and page returns to `View` mode

Rules:
- Do not auto-save critical settings
- Do not leave users guessing where “save” happens
- Do not provide multiple edit entry points for the same setting
- Never use inline editing. Use a modal or navigate to a dedicated edit page depending on screen complexity.

---

## Conditional UI by Mode (Critical)

For mode-driven configurations (example: `Access Mode`), enforce:

1. Mutually exclusive modes
- `URL Token`
- `Email List`
- `Domain`

2. Mode-specific fields only
- `Email List`: show portal user management
- `Domain`: show allowed domains
- `URL Token`: show link/token controls

3. Mode-specific actions only
- Never show actions that do not apply to the current mode

---

## URL and Shareability Guidelines

When a feature exposes a portal link:

1. Build URL from current app origin + route + current slug
2. Show the final URL as read-only
3. Provide a `Copy` button
4. Show success feedback after copy

Do not hardcode hostnames or stale base URLs.

---

## Forms and Validation Rules

1. Show constraints before typing
- Example: minimum length in helper text or placeholder

2. Validate on blur + on submit
- If field loses focus and is invalid, show inline error immediately

3. Keep labels and errors explicit
- Error text near the field
- Error style on label/input

4. Validate on submit (global policy)
- Keep `Save`/`Submit` enabled by default (only disable for loading/pending requests).
- On click, validate all required fields and show inline errors in red.
- Never fail silently: always show what is missing or invalid.
- Do not use "disabled until complete" as the primary validation pattern.

---

## Tooltip Rules (Clarity First)

1. Icon-only buttons must have tooltip
- If a button has no visible text label, it must expose a clear tooltip.
- `aria-label` is required for accessibility, but does not replace the visible tooltip requirement.

2. Ambiguous tags/badges must have tooltip
- If a tag/badge appears without nearby label text that explains what it represents, add a tooltip.
- Typical examples: `status`, `risk`, `priority`, or short numeric badges shown in cards.

3. Table exception
- In dense tables, tooltip is optional when the column header already explains the badge meaning.
- Outside tables (cards/panels/detail headers), ambiguous badges require tooltip by default.

4. Tooltip content quality
- Keep text short and explicit (what it is, not just the value).
- Example: use "Risk level: High" instead of only "High".

5. List action buttons pattern
- In list/table rows, action buttons should be icon-only by default.
- Every icon-only action must have a real visible tooltip describing the action.
- Keep `aria-label`, but do not rely on it as tooltip replacement.

6. Confirm destructive or direct-change actions
- Any list action that performs direct change (`POST`/`PUT`/`DELETE`) must require confirmation before execution.
- Apply this to delete, approve/reject, activate/deactivate, set default, and similar state-changing actions.

---

## Date Format Standard

1. Use `YYYY/MM/DD` for all visible dates in app screens
- Applies to tables, cards, detail views, badges, exports previews, and summaries.
- Do not use locale-dependent date formats (e.g., `MM/DD/YYYY` or `DD/MM/YYYY`) in UI.

2. Include time only when needed
- If date-time is required, keep date first: `YYYY/MM/DD HH:mm`.

---

## Long Content and Attachments

For potentially large text or files:

1. Show short preview in list/table
2. Provide `View` action to open full content in modal
3. For attachments:
- Show uploaded files before submit
- Allow remove before submit
- Allow view/download after submit

Users must always be able to verify what was uploaded.

---

## Navigation Consistency

1. Use one global navigation hierarchy
2. Do not duplicate the same nav options in top toolbar and sidebar
3. Keep local page tabs focused on that page only

If global nav already exists on the left, do not re-create it in page header.

---

## UX Anti-Patterns to Avoid

- Multiple ways to edit the same setting
- Actions that do not match current mode
- Internal fields with no user value (example: raw access counters/tokens)
- Icon-only actions without tooltip
- Ambiguous status/risk/priority badges without tooltip context
- Hidden save behavior
- Broken generated URLs
- No way to view long descriptions or uploaded files
- Submitting forms without visible validation feedback
- Disabling `Save`/`Submit` until all fields are complete as the default validation pattern
- Using card/panel grids for dense operational listings

---

## Key Use Cases (Client Area)

### Use Case A: Add Contract

Expected flow:
1. Open client detail
2. Go to contracts section
3. Click `Add Contract`
4. Complete minimal required fields + upload file
5. Save
6. See new contract in list immediately

Must-have UX:
- Clear required fields
- Upload status visible
- Post-save confirmation

### Use Case B: Add Portal User

Expected flow:
1. Open client detail
2. Open portal access section
3. Select `Email List` mode
4. Click `Add portal user`
5. Save
6. User appears in allowed list

Must-have UX:
- Action visible only in `Email List` mode
- Fast validation for email format
- Deterministic save feedback

---

## Definition of Done for Any New Screen

- [ ] Primary goal/action is obvious
- [ ] Single edit path per setting
- [ ] Correct mode-based conditional UI
- [ ] Entity lists use tables by default (with justified exception if not)
- [ ] Visible dates use `YYYY/MM/DD` format
- [ ] Clear save and error feedback
- [ ] Full loading/empty/error states
- [ ] Long text and attachments are viewable
- [ ] URL generation uses current environment
- [ ] No duplicated global navigation
- [ ] Icon-only buttons have tooltip
- [ ] Ambiguous badges/tags have tooltip (except clear table-column context)
- [ ] EN/ES translations complete
- [ ] Mobile and keyboard interaction validated

---

## Implementation Notes

Recommended building blocks:
- `Card` for sectioning
- `Dialog` for edit/view flows
- `Form` + inline error components for validation
- `Toast` for action feedback

Always pair UX decisions with:
1. API contract review
2. Frontend state/edge-case handling
3. Integration tests for critical flows
