# Tasks: F3 — Frontend UX

**Requirement:** [../../requirements.md](../../requirements.md)
**Design:** [design.md](design.md)
**Date:** 2026-02-18
**Total Tasks:** 10
**Complexity:** Medium

## Summary

| Phase | Tasks | Complexity |
|-------|-------|------------|
| Types | 1 | S |
| Pages — Settings | 1 | M |
| Pages — Detail Card | 1 | M |
| Routing | 1 | S |
| Sidebar | 1 | S |
| i18n — English | 1 | S |
| i18n — Spanish | 1 | S |
| Verification | 1 | S |

## Phase 1: Types

### TASK-001: Add TypeScript types
**Phase:** Types
**Complexity:** S
**Dependencies:** None
- [x] Edit `web/app/src/types/index.ts`
- [x] Add `CompanyClassificationConfig` interface per design
- [x] Add `AIClassificationData` interface per design
- [x] Acceptance: types importable, match API response structure

## Phase 2: Pages

### TASK-002: Create ClassificationSettingsPage
**Phase:** Pages
**Complexity:** M
**Dependencies:** TASK-001
- [x] Create `web/app/src/pages/admin/ClassificationSettingsPage.tsx`
- [x] Follow `AssignmentAISettingsPage` pattern per design
- [x] Form fields: enable toggle, provider dropdown, model input, threshold, prompt textarea, timeout
- [x] `isDirty` tracking, save button disabled when clean
- [x] `useQuery` for GET, `useMutation` for PUT
- [x] Toast on save success/error
- [x] All text via i18n keys
- [x] Acceptance: page loads config, saves changes, admin only

### TASK-003: Add AI Classification card to RequestDetailPage
**Phase:** Pages
**Complexity:** M
**Dependencies:** TASK-001
- [x] Edit `web/app/src/pages/technician/RequestDetailPage.tsx`
- [x] Add card component per design — follow `AutoAssignmentCard` pattern
- [x] Render when `request.data?.ai_classification?.ai_used === true`
- [x] Technician+ only visibility
- [x] Display all fields per design table
- [x] Header badge: "AI Classified" when `ai_used === true`
- [x] Update priority scoring card: add `ai_hint_weight` row
- [x] All text via i18n keys
- [x] Acceptance: card renders correctly with mock data

## Phase 3: Routing & Navigation

### TASK-004: Add route
**Phase:** Routing
**Complexity:** S
**Dependencies:** TASK-002
- [x] Edit `web/app/src/router.tsx`
- [x] Add lazy import for `ClassificationSettingsPage`
- [x] Add route `settings/request-classification` with admin RequireRole guard
- [x] Acceptance: page accessible at `/settings/request-classification`

### TASK-005: Add sidebar nav item
**Phase:** Sidebar
**Complexity:** S
**Dependencies:** None
- [x] Edit `web/app/src/components/layout/Sidebar.tsx`
- [x] Add item in `section_management` per design
- [x] Admin only
- [x] Acceptance: nav item visible to admins, links to correct path

## Phase 4: i18n

### TASK-006: English i18n keys
**Phase:** i18n
**Complexity:** S
**Dependencies:** None
- [x] Edit `web/app/src/locales/en.ts`
- [x] Add all ~30 keys per design i18n section
- [x] Acceptance: no missing translation warnings

### TASK-007: Spanish i18n keys
**Phase:** i18n
**Complexity:** S
**Dependencies:** None
- [x] Edit `web/app/src/locales/es.ts`
- [x] Add all ~30 keys translated to Spanish
- [x] Acceptance: no missing translation warnings

## Verification

### TASK-008: Verify F3
- [x] TypeScript compiles: `cd web/app && npx tsc --noEmit`
- [x] Build succeeds: `cd web/app && npm run build`
- [x] No hardcoded strings (all text uses i18n keys)

## Progress Tracking
- [x] Mark all tasks done
- [x] Update `slicing.md` — F3 status to Done
- [x] Update `docs/product/roadmap.md` — E13 status to Done
