# Tasks: F3 — Frontend UX for Settings & Assignment Visibility

## Implementation Tasks

### 1. TypeScript Types
- [x] Add `EquipmentProfile`, `EquipmentProfileItem`, `CompanyAIConfig`, `FallbackReason` types to `web/app/src/types/index.ts`

### 2. Equipment Profiles Page
- [x] Create `web/app/src/pages/admin/EquipmentProfilesPage.tsx`
  - List profiles with filters (department, role, active/all)
  - Create profile form: select department, role, add items (asset type + specs)
  - Edit profile items
  - Activate/deactivate toggle
  - Delete with confirmation dialog
  - Dual-check authorization (admin OR department manager) enforced by backend

### 3. Assignment AI Settings Page
- [x] Create `web/app/src/pages/admin/AssignmentAISettingsPage.tsx`
  - Provider selector (OpenAI / Groq dropdown)
  - Prompt template textarea
  - Optional model field
  - Save button with toast feedback
  - Admin only

### 4. Department Manager Assignment
- [x] Edit `web/app/src/pages/admin/DepartmentsPage.tsx`
  - Add manager user picker (dropdown/select) per department row
  - Show current manager email/name
  - Assign/remove with confirmation

### 5. Assignment Explainability
- [x] Edit `web/app/src/pages/technician/RequestDetailPage.tsx`
  - Show profile assignment metadata (if `request.data.auto_assignment` exists):
    - Matched assets, fallback reasons
    - AI badge if AI tie-break was used
  - Status badge: Matched/Partial/Fallback/Skipped
- [x] Edit `web/app/src/pages/technician/AssetDetailPage.tsx` — Deferred (no profile_assignment events exist yet in backend event history)

### 6. Routing
- [x] Add route `/settings/equipment-profiles` — Admin + super_admin
- [x] Add route `/settings/assignment-ai` — Admin only

### 7. Navigation
- [x] Add "Equipment Profiles" to Sidebar Management section (admin + super_admin roles)
- [x] Add "Assignment AI" to Sidebar Management section (admin only)
- [x] Update super_admin filter if needed

### 8. i18n
- [x] Add English keys to `web/app/src/locales/en.ts` (~45 keys)
  - Profile CRUD labels, AI settings labels, fallback reason translations, assignment metadata labels
- [x] Add Spanish keys to `web/app/src/locales/es.ts` (~45 keys)

### 9. Verification
- [x] TypeScript compiles without errors (`npx tsc --noEmit`)
- [x] Build succeeds (`npm run build`)
- [x] All text uses i18n keys (no hardcoded strings)

### 10. Progress Tracking
- [x] Mark all tasks done
- [x] Update `slicing.md` — F3 status to Done
- [x] Update `docs/product/roadmap.md` — E11 status to Done
