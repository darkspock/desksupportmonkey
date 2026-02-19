# Tasks: F4 — Frontend UX

## Implementation Tasks

### 1. TypeScript Types
- [x] Edit `web/app/src/types/index.ts`
  - Extended `RequestType` with: `'repair' | 'configuration' | 'access_request'` (done in F2)
  - Extended `RequestStatus` with: `'pending_approval'` (done in F2)
  - Added `RequestSubtype` type with all 16 subtype string literals
  - Added `VALID_SUBTYPES` mapping: `Record<RequestType, RequestSubtype[]>` for frontend validation
  - Added `subtype?: string | null` field to `ServiceRequest` interface
  - Added `priority_weight?: number` field to `Department` interface

### 2. New Request Form — Subtype Selector
- [x] Edit `web/app/src/pages/employee/NewRequestPage.tsx`
  - Added new request types to the type dropdown: repair, configuration, access_request
  - Added subtype dropdown below type, shown only when selected type has subtypes
  - Subtype options populated dynamically from `VALID_SUBTYPES[selectedType]`
  - Subtype cleared when type changes
  - Sends `subtype` in POST /requests body when selected
  - Uses i18n keys for all new type/subtype labels

### 3. Request Queue — Subtype Filter and Badge
- [x] Edit `web/app/src/pages/technician/RequestQueuePage.tsx`
  - Added subtype filter dropdown (populated based on selected type filter, or all subtypes)
  - Passes `subtype` query param to `GET /requests`
  - Shows subtype in parentheses next to type in list items (when present)
  - Added "Pending Approval" to status filter options
  - Added new types (repair, configuration, access_request) to type filter

### 4. Request Detail — Subtype, Scoring, Approval Actions
- [x] Edit `web/app/src/pages/technician/RequestDetailPage.tsx`
  - Shows subtype badge next to type badge (when present)
  - Shows priority scoring breakdown card (when `request.data.priority_scoring` exists, tech only):
    - Type weight, subtype weight, department weight, role weight, raw score
  - Added approval actions for `pending_approval` status (visible to technicians+):
    - "Approve" button → `POST /requests/{id}/approve`
    - "Reject" button → shows inline input for rejection reason → `POST /requests/{id}/reject`
  - Added `isPendingApproval` flag to conditionally show approval UI
  - Status badge shows pending_approval

### 5. My Requests — Subtype and Approval Status
- [x] Edit `web/app/src/pages/employee/MyRequestsPage.tsx`
  - Shows subtype in request list (when present, as small gray text)
  - `pending_approval` status badge works via StatusBadge component

### 6. Departments Page — Priority Weight Editor
- [x] Edit `web/app/src/pages/admin/DepartmentsPage.tsx`
  - Added "Priority Weight" column to the table header
  - Shows current weight value as a clickable button
  - Inline editor: number input (-1 to +2) with save/cancel
  - Sends `priority_weight` in PUT /departments/{id} body
  - Toast on success/error

### 7. i18n — English
- [x] Edit `web/app/src/locales/en.ts`
  - New type enums: `enum.repair`, `enum.configuration`, `enum.access_request`
  - New status enum: `enum.pending_approval`
  - All subtype enums (16 keys)
  - New request form: `page.new_request.subtype`, `page.new_request.select_subtype`
  - Request detail — approval: 9 keys
  - Request detail — scoring: 6 keys
  - Request queue: `page.request_queue.all_subtypes`
  - Departments: 3 keys for priority weight

### 8. i18n — Spanish
- [x] Edit `web/app/src/locales/es.ts`
  - Same keys as English section, translated

### 9. Verification
- [x] TypeScript compiles without errors (`npx tsc --noEmit` passes)
- [x] Build succeeds (`npm run build` — ✓ built in 1.29s)
- [x] No hardcoded strings (all text uses i18n keys)

### 10. Progress Tracking
- [x] Mark all F4 tasks done
- [ ] Update `slicing.md` — F4 status to Done
- [ ] Update `docs/product/roadmap.md` — E12 status to Done
