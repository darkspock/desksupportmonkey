# E41: Per-Item Equipment Budgets & Procurement Manager Role — Tasks

## Feature 1: Procurement Manager Role

### Backend
- [ ] F1.1 Add `PROCUREMENT_MANAGER = "procurement_manager"` to `UserRole` enum in `src/auth_bc/user/domain/enums.py`
- [ ] F1.2 Update role level hierarchy: EMPLOYEE=1, TECHNICIAN=2, PROCUREMENT_MANAGER=3, ADMIN=4, SUPER_ADMIN=5
- [ ] F1.3 Create Alembic migration to update existing role column values (admin 3→4, super_admin 4→5 are enum string values so no data migration needed — but verify)
- [ ] F1.4 Update PO approve endpoint to accept `PROCUREMENT_MANAGER` role (currently requires ADMIN)
- [ ] F1.5 Update request approve authorization to also allow procurement_manager
- [ ] F1.6 Add procurement_manager to seed data script
- [ ] F1.7 Update any role validation/checks that hardcode role lists

### Frontend
- [ ] F1.8 Add `'procurement_manager'` to `UserRole` type in `web/app/src/types/index.ts`
- [ ] F1.9 Update Sidebar.tsx to show Operations + Procurement pages for procurement_manager
- [ ] F1.10 Add i18n translations for procurement_manager role (EN: "Procurement Manager", ES: "Responsable de compras")
- [ ] F1.11 Update role selectors in EquipmentProfilesPage and any role dropdowns
- [ ] F1.12 Update any frontend role-check utilities/guards

## Feature 2: Department Budget Enforcement Toggle

### Backend
- [ ] F2.1 Add `budget_enforcement_enabled: bool = False` field to Department domain entity
- [ ] F2.2 Add `budget_enforcement_enabled` column to DepartmentModel
- [ ] F2.3 Create Alembic migration for new column (default False)
- [ ] F2.4 Update Department mapper/serialization to include new field
- [ ] F2.5 Update department PATCH/update endpoint to accept `budget_enforcement_enabled`
- [ ] F2.6 Update BudgetChecker to skip budget check when department has `budget_enforcement_enabled=False`
- [ ] F2.7 Update department GET response schema to include `budget_enforcement_enabled`

### Frontend
- [ ] F2.8 Add `budget_enforcement_enabled` to Department type in `types/index.ts`
- [ ] F2.9 Add toggle switch on DepartmentsPage for budget enforcement
- [ ] F2.10 Add i18n translations for budget enforcement toggle

## Feature 3: Per-Asset-Type Budget on Equipment Profiles

### Backend
- [ ] F3.1 Add `budget_cents: Optional[int] = None` to EquipmentProfileItem domain entity
- [ ] F3.2 Add `budget_cents` column to EquipmentProfileItemModel (nullable integer)
- [ ] F3.3 Create Alembic migration for new column
- [ ] F3.4 Update equipment profile create/update commands to accept `budget_cents`
- [ ] F3.5 Update equipment profile GET response to include `budget_cents`
- [ ] F3.6 Update equipment profile mapper/serialization

### Frontend
- [ ] F3.7 Add `budget_cents` to EquipmentProfileItem type in `types/index.ts`
- [ ] F3.8 Add budget input field per item in EquipmentProfilesPage form
- [ ] F3.9 Display budget in profile item list with currency formatting
- [ ] F3.10 Add i18n translations for budget field labels

## Feature 4: Budget Indicator on Equipment Requests

### Backend
- [ ] F4.1 Create query to check per-item budget for a given department/role/asset_type
- [ ] F4.2 Create GET endpoint `/api/v1/equipment-profiles/budget-check` that returns budget status for requested equipment
- [ ] F4.3 Include budget info in request detail response (when request is new_equipment type)

### Frontend
- [ ] F4.4 Call budget-check endpoint from NewRequestPage when equipment type is selected
- [ ] F4.5 Display "Within budget" / "Over budget" badge on NewRequestPage
- [ ] F4.6 Show budget indicator on request detail page for new_equipment requests
- [ ] F4.7 Add i18n translations for budget indicator labels

## Testing
- [ ] T1 Unit tests for updated UserRole enum and hierarchy
- [ ] T2 Unit tests for BudgetChecker with enforcement toggle
- [ ] T3 Integration tests for procurement_manager role access on PO endpoints
- [ ] T4 Integration tests for department budget_enforcement_enabled toggle
- [ ] T5 Integration tests for equipment profile budget_cents CRUD
- [ ] T6 Integration tests for budget-check endpoint
