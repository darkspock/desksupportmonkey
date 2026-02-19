# Feature: API Keys Frontend Page

**Parent Epic:** [E35 - MCP Server](../../requirements.md)
**Feature #:** F7
**Dependencies:** F0 (API Key Management -- backend endpoints)
**Complexity:** M

---

## Scope

### Included

A new React frontend page for admin users to create and manage API keys through the web UI.

**Page:** `/settings/api-keys` (or equivalent route within the admin section)

**UI Components:**
- API key list table displaying: name, created_at, last_used_at, status (active/revoked)
- "Create API Key" button and form (name input field)
- One-time raw key display modal with copy-to-clipboard button (shown immediately after creation)
- Revoke key confirmation dialog
- Empty state when no API keys exist
- Loading and error states

**API Client:**
- API client functions for the 3 backend endpoints:
  - `POST /api/v1/auth/api-keys` -- create API key
  - `GET /api/v1/auth/api-keys` -- list API keys
  - `DELETE /api/v1/auth/api-keys/{key_id}` -- revoke API key
- TanStack React Query hooks for data fetching and cache invalidation

**i18n:**
- English (EN) and Spanish (ES) translation strings for all page text, labels, buttons, errors, and confirmation dialogs
- Strings added to existing `web/app/src/locales/en.ts` and `web/app/src/locales/es.ts`

**Design:**
- Responsive layout (desktop and mobile)
- Follows existing design system tokens (colors, spacing, typography, shadows)
- Consistent with the visual style of existing admin pages (e.g., UsersPage, DepartmentsPage)

### Excluded

- MCP server and MCP tools (F1-F6)
- All backend work: API key entity, migration, repository, and HTTP endpoints (F0)
- API key usage analytics or audit logs
- API key permission scoping (keys inherit user's full role)
- Super Admin company-level key management

---

## User Value

Admin users can create, view, and revoke API keys directly from the web interface, without needing CLI tools or direct API calls. This enables:
- **Self-service MCP setup:** An admin creates an API key, copies it, and pastes it into Claude Desktop or Cursor configuration.
- **Security management:** Admins can see which keys exist, when they were last used, and revoke compromised or unused keys.
- **Key lifecycle visibility:** The last_used_at timestamp helps admins identify stale keys that should be cleaned up.

---

## Acceptance Criteria

### Navigation
- [ ] Admin users can navigate to the API Keys page from the settings/admin navigation
- [ ] The page is accessible only to Admin and Super Admin roles (Employee and Technician cannot access)
- [ ] Navigation link/menu item is visible only to authorized roles

### List API Keys
- [ ] Page displays a table/list of the user's API keys
- [ ] Each row shows: name, created_at (formatted date), last_used_at (formatted date or "Never"), status badge (Active/Revoked)
- [ ] Keys are sorted by created_at descending (newest first)
- [ ] Loading spinner shown while fetching data
- [ ] Empty state message shown when no keys exist (e.g., "No API keys yet. Create one to connect AI assistants.")
- [ ] Error state shown if the API call fails

### Create API Key
- [ ] "Create API Key" button opens a creation form/dialog
- [ ] Form requires a name field (e.g., "Claude Desktop", "Cursor")
- [ ] Name field has appropriate validation (required, max length)
- [ ] On success, a modal displays the raw API key with prominent copy-to-clipboard button
- [ ] Modal includes a warning that the key will not be shown again
- [ ] After closing the modal, the key list refreshes to include the new key
- [ ] The raw key is not stored in frontend state after the modal is dismissed
- [ ] If user has 10 active keys, creation is disabled with an explanatory message

### Copy to Clipboard
- [ ] Copy button copies the raw API key to the system clipboard
- [ ] Visual feedback confirms the copy action (e.g., button text changes to "Copied!" briefly)
- [ ] Works in all modern browsers (Chrome, Firefox, Safari, Edge)

### Revoke API Key
- [ ] Each active key row has a "Revoke" button/action
- [ ] Clicking "Revoke" opens a confirmation dialog (e.g., "Are you sure you want to revoke this key? This action cannot be undone.")
- [ ] On confirmation, the key is revoked and the list refreshes
- [ ] Revoked keys appear with a "Revoked" status badge (visually distinct from "Active")
- [ ] Revoked keys do not have a "Revoke" button (action is not reversible)
- [ ] Appropriate toast/notification shown on successful revocation

### i18n
- [ ] All text, labels, buttons, error messages, and confirmation dialogs use translation keys
- [ ] English translations added to `web/app/src/locales/en.ts`
- [ ] Spanish translations added to `web/app/src/locales/es.ts`
- [ ] Page renders correctly in both languages

### Design & Responsiveness
- [ ] Page layout follows existing admin page patterns (consistent header, spacing, table style)
- [ ] Uses existing design system tokens (colors, typography, spacing, border-radius, shadows)
- [ ] Responsive: table/list is usable on mobile viewports (stacked layout or horizontal scroll)
- [ ] Status badges use appropriate colors (green for Active, gray/red for Revoked)
- [ ] Follows existing component patterns (buttons, modals, dialogs, form inputs)

### Technical Quality
- [ ] TypeScript compiles without errors
- [ ] API client functions use the existing `web/app/src/lib/api.ts` patterns
- [ ] React Query hooks follow existing TanStack Query conventions (query keys, mutations, cache invalidation)
- [ ] No hardcoded strings (all user-facing text uses i18n)
- [ ] Component follows existing file organization patterns

---

## Technical Scope

### Entities (owned)

None. This feature creates no backend entities (ApiKey is created in F0). Frontend types/interfaces for the API key data shape are created in this feature.

### Entities (used)

- `ApiKey` (backend, via API) -- id, name, created_at, last_used_at, is_active

### Key Components

| Component | Action | Description |
|-----------|--------|-------------|
| `web/app/src/pages/admin/ApiKeysPage.tsx` | Create | Main page component with key list, create, and revoke functionality |
| `web/app/src/lib/api.ts` or new `api-keys.ts` | Modify/Create | API client functions for create, list, revoke endpoints |
| `web/app/src/types/index.ts` | Modify | Add ApiKey TypeScript interface |
| `web/app/src/locales/en.ts` | Modify | Add English translation strings for API keys page |
| `web/app/src/locales/es.ts` | Modify | Add Spanish translation strings for API keys page |
| `web/app/src/App.tsx` or router config | Modify | Add route for the API keys page |
| Navigation component | Modify | Add "API Keys" link in admin settings navigation |

---

## Notes

- The raw API key is security-sensitive. It must be displayed only once in the creation modal and cleared from component state when the modal closes. It should never be logged, cached, or persisted in localStorage/sessionStorage.
- The copy-to-clipboard feature should use the Clipboard API (`navigator.clipboard.writeText()`) with a fallback for older browsers if the existing codebase supports them.
- The page should visually communicate the importance of copying the key immediately. Consider using a warning icon, bold text, or a colored banner in the modal.
- The 10 active key limit per user should be communicated proactively: if the user has 9 keys, show a hint. If they have 10, disable the create button and explain why.
- This page is independent of the MCP server itself. It manages API keys that can be used for MCP authentication, but the page does not reference MCP directly in its UI (keys could theoretically be used for other API integrations in the future).
- Follow the same component patterns visible in existing admin pages like `UsersPage.tsx`, `DepartmentsPage.tsx`, and `CompanySettingsPage.tsx` for consistency.
