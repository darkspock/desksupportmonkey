# Tasks: F7 — API Keys Frontend Page

## Implementation Tasks

### 1. TypeScript Types
- [x] Add `ApiKey` and `CreatedApiKey` interfaces to `web/app/src/types/index.ts`

### 2. Page Component
- [x] Create `web/app/src/pages/admin/ApiKeysPage.tsx`
- [x] List API keys in table (name, created_at, last_used_at, status badge)
- [x] Create form with name input
- [x] Raw key modal with copy-to-clipboard and warning
- [x] Revoke confirmation dialog
- [x] 10-key limit enforcement (disable create, show message)
- [x] Loading, error, and empty states

### 3. Routing
- [x] Add lazy import and route in `web/app/src/router.tsx`
- [x] Role-restricted to Admin and Super Admin

### 4. Navigation
- [x] Add "API Keys" nav item in `Sidebar.tsx` under Management section
- [x] Visible to admin and super_admin roles
- [x] Super admin filter updated to include `/settings/api-keys`

### 5. i18n
- [x] English translations added to `web/app/src/locales/en.ts` (27 keys)
- [x] Spanish translations added to `web/app/src/locales/es.ts` (27 keys)

### 6. Verification
- [x] TypeScript compiles without errors
- [x] All text uses i18n keys (no hardcoded strings)
- [x] Follows existing page patterns (DepartmentsPage, UsersPage)

### 7. Progress Tracking
- [x] Mark all tasks done
- [x] Update `slicing.md` — F7 status to Done
