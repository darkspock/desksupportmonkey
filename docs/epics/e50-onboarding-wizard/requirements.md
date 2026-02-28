# Epic: E50 - Onboarding Wizard

**Type:** Epic
**Status:** Draft
**Created:** 2026-02-28

## Business Alignment

- **Objective:** Churn reduction / Activation rate
- **KPI Target:** Reduce time-to-first-value from ~30 min to < 5 min. Increase activation rate (companies that configure at least one module within 24h) from estimated 40% to 80%.
- **Evidence:** DSM has 50+ features across 9 functional modules. New admins land on a full sidebar with 30+ menu items covering service desk, assets, procurement, compliance, security, change management, etc. This overwhelms SMB users who only need 2-3 modules initially. Competitors like InvGate use progressive disclosure to reduce perceived complexity.

## Problem Statement

### Current Situation
When a new company admin logs in for the first time, they see the complete application interface. All modules are visible: service requests, asset inventory, procurement, vendors, compliance (NIS2/DORA/ISO 27001/GDPR), security incidents, vulnerability management, change management, SLA, maintenance, shipping, knowledge base, etc. There is no guidance on where to start or which modules are relevant to their business.

### Pain Points
1. **Cognitive overload**: 30+ sidebar items visible from day one. The admin doesn't know what half of them do.
2. **No sector context**: A financial services company needs DORA compliance; a healthcare company needs different frameworks. The platform doesn't ask and can't suggest.
3. **Feature discovery is accidental**: Admins don't know which modules exist or which ones would benefit them. They discover features randomly or never.
4. **Compliance gap**: Admins must manually navigate to Settings > Compliance Controls and know which frameworks apply to their sector. Most don't.

### Impact if Not Solved
- High initial churn: admins feel the tool is "too complex for us"
- Low module adoption: companies use 1-2 modules when they could benefit from 4-5
- Compliance blind spot: companies in regulated sectors don't enable relevant frameworks

## Proposed Solution

A 3-step onboarding wizard that runs on the admin's first login. The wizard:

1. **Asks the company's industry sector** -- to tailor suggestions
2. **Suggests compliance frameworks** -- based on the selected sector
3. **Asks which functional modules to activate** -- hides everything else from the sidebar

The result: a clean, focused interface from day one. Admins can always re-enable hidden modules later via Settings > Navigation Visibility (existing feature).

### User Stories

#### US-001: Admin Sees Onboarding on First Login
**As an** Admin logging in for the first time
**I want** to be guided through a setup wizard
**So that** I can configure the platform for my company without feeling overwhelmed

**Acceptance Criteria:**
- [ ] Onboarding wizard appears automatically on admin's first login
- [ ] Wizard does NOT appear for employees, technicians, or super admins
- [ ] Wizard does NOT appear on subsequent logins (flag persisted)
- [ ] Wizard can be skipped entirely ("Skip, I'll configure later")
- [ ] If skipped, all modules remain visible (current behavior)

#### US-002: Admin Selects Company Sector
**As an** Admin
**I want** to select my company's industry sector
**So that** the platform can tailor its recommendations

**Acceptance Criteria:**
- [ ] Step 1 presents a list of industry sectors to choose from
- [ ] Exactly one sector can be selected
- [ ] The selected sector is saved to the company profile
- [ ] Sector can be changed later from company settings

**Industry sectors:**

| Sector ID | Label (EN) | Label (ES) |
|-----------|------------|------------|
| `financial_services` | Financial Services | Servicios Financieros |
| `healthcare` | Healthcare | Salud |
| `government` | Government / Public Sector | Gobierno / Sector Publico |
| `education` | Education | Educacion |
| `technology` | Technology | Tecnologia |
| `manufacturing` | Manufacturing | Manufactura |
| `retail` | Retail / E-Commerce | Retail / Comercio Electronico |
| `energy` | Energy / Utilities | Energia / Servicios Publicos |
| `telecommunications` | Telecommunications | Telecomunicaciones |
| `professional_services` | Professional Services / Consulting | Servicios Profesionales / Consultoria |
| `logistics` | Logistics / Transportation | Logistica / Transporte |
| `other` | Other | Otro |

#### US-003: Platform Suggests Compliance Frameworks
**As an** Admin who selected a sector
**I want** to see which compliance frameworks are recommended for my industry
**So that** I can enable the right ones without having to research which apply

**Acceptance Criteria:**
- [ ] Step 2 shows compliance frameworks with a recommendation badge for sector-relevant ones
- [ ] Admin can check/uncheck any framework (recommendations are suggestions, not mandatory)
- [ ] Selected frameworks are enabled using the same frontend seeding logic as `ComplianceControlsPage.tsx` (no new backend endpoint)
- [ ] If no frameworks are selected, compliance section is hidden from the sidebar

**Sector-to-Framework Mapping:**

| Sector | Recommended Frameworks |
|--------|----------------------|
| Financial Services | DORA, NIS2, ISO 27001, GDPR |
| Healthcare | NIS2, ISO 27001, GDPR |
| Government / Public Sector | NIS2, ISO 27001, GDPR |
| Education | GDPR, ISO 27001 |
| Technology | ISO 27001, GDPR, NIS2 |
| Manufacturing | NIS2, ISO 27001 |
| Retail / E-Commerce | GDPR, ISO 27001 |
| Energy / Utilities | NIS2, DORA, ISO 27001 |
| Telecommunications | NIS2, ISO 27001, GDPR |
| Professional Services | GDPR, ISO 27001 |
| Logistics / Transportation | NIS2, GDPR |
| Other | *(none pre-selected, all available)* |

#### US-004: Admin Selects Active Modules
**As an** Admin
**I want** to choose which platform modules my company will use
**So that** my team only sees relevant features in the sidebar

**Acceptance Criteria:**
- [ ] Step 3 presents functional modules as toggleable cards/options
- [ ] Each module has a short description of what it does
- [ ] "Service Desk" (requests) is pre-selected and cannot be deactivated (core module)
- [ ] Deactivated modules are hidden from the sidebar for all roles in the company
- [ ] Module visibility is persisted using the existing `hidden_nav_items` mechanism
- [ ] Admins can change module visibility later from Settings > Navigation Visibility

**Module groups and their associated nav paths:**

| Module | Description (EN) | Nav Paths Hidden When Off |
|--------|-----------------|--------------------------|
| Service Desk | Service requests, queue, SLA | *(always on -- core, includes `/sla/policies`, `/sla/dashboard`)* |
| Asset Inventory | Hardware tracking, CMDB, labels | `/assets`, `/cmdb/dashboard`, asset-related settings |
| Procurement | Purchase orders, vendors, budgets | `/purchase-orders`, `/vendors`, `/vendors/supply-chain`, procurement settings |
| Knowledge Base | Articles, categories, AI suggestions | `/knowledge-base`, `/kb`, `/kb/categories` |
| Compliance & Audit | Frameworks, controls, audit trail | `/compliance/dashboard`, `/settings/compliance`, `/audit` |
| Security | Incidents, risks, vulnerabilities | `/incidents`, `/incidents/dashboard`, `/risks`, `/risks/dashboard`, `/vulnerabilities`, `/vulnerabilities/dashboard` |
| Change Management | Change requests, approval workflows | `/changes`, `/changes/dashboard` |
| Maintenance | Scheduled maintenance, templates | `/maintenance`, `/my/maintenance`, `/maintenance-templates` |
| Logistics | Shipping, appointments | `/shipments`, `/my/shipments`, `/my/appointments`, `/my/tasks/appointments`, `/calendar` |

**Always visible (not tied to any module):** `/billing`, `/reports` -- these are admin-level features that remain visible regardless of module selection.

#### US-005: Onboarding Completion
**As an** Admin who completed the wizard
**I want** to see a summary of my choices and start using the platform
**So that** I feel confident the setup is correct

**Acceptance Criteria:**
- [ ] Final step shows a summary: sector, enabled frameworks, active modules
- [ ] "Finish Setup" button applies all configurations and redirects to dashboard
- [ ] A welcome toast/notification confirms the setup was applied
- [ ] The sidebar immediately reflects the module selection (hidden items gone)

#### US-006: Admin Re-runs Onboarding Wizard
**As an** Admin
**I want** to re-run the setup wizard from Company Settings
**So that** I can reconfigure my company's sector, frameworks, and modules without navigating each setting individually

**Acceptance Criteria:**
- [ ] Company Settings page has a "Re-run setup wizard" button
- [ ] Clicking it opens the same 3-step wizard with current values pre-filled
- [ ] Completing it overwrites previous sector, framework, and module settings
- [ ] Wizard always shows all 3 steps (does not skip any, even if sector is already set)

## Entities & State Machines

### Company (existing entity -- modified)
New field: `sector` (nullable string enum, set during onboarding or company settings).

### OnboardingStatus (new concept -- lightweight)
Not a separate entity. A flag on the company or admin user indicating onboarding was completed. Could be:
- A `onboarding_completed_at` timestamp on Company, OR
- A `has_completed_onboarding` boolean on Company

**States:** `pending` (null/false) -> `completed` (timestamp/true). One-way transition. No further states needed.

### No new entities required
The onboarding wizard orchestrates existing systems:
- Saves `sector` to Company
- Calls existing compliance controls API to enable/disable frameworks
- Calls existing nav visibility API to set `hidden_nav_items`

## Use Cases

### UC-001: Happy Path -- Full Onboarding
**Actor:** Admin (first login)
**Preconditions:** Admin has never completed onboarding for this company
**Postconditions:** Company has sector, compliance frameworks enabled, modules configured

1. Admin logs in for the first time
2. System detects `onboarding_completed_at` is null -> shows wizard
3. Step 1: Admin selects "Financial Services"
4. Step 2: System pre-checks DORA, NIS2, ISO 27001, GDPR. Admin unchecks GDPR (not their concern)
5. Step 3: Admin enables Service Desk, Asset Inventory, Compliance & Audit. Disables the rest.
6. Summary screen shows choices. Admin clicks "Finish Setup"
7. System saves sector, enables 3 frameworks, hides 5 modules from sidebar
8. Admin lands on dashboard with a clean, focused sidebar

### UC-002: Skip Onboarding
**Actor:** Admin
1. Admin sees wizard, clicks "Skip, I'll configure later"
2. System marks onboarding as skipped (sets flag so wizard doesn't reappear)
3. All modules remain visible. No sector saved. No frameworks enabled.
4. Admin can configure everything manually from settings at any time.

### UC-003: Second Admin Logs In
**Actor:** Second admin for the same company
1. Second admin logs in
2. System checks: company's `onboarding_completed_at` is already set
3. No wizard shown. Second admin sees the sidebar as configured by the first admin.

### UC-004: Admin Changes Sector Later
**Actor:** Admin
1. Admin navigates to Settings > Company
2. Admin changes sector from "Financial Services" to "Healthcare"
3. System saves new sector. Does NOT auto-change frameworks or module visibility.
4. Admin receives a suggestion: "Your sector changed. Review your compliance frameworks in Settings > Compliance Controls."

### UC-005: Error -- API Failure During Save
**Actor:** Admin
1. Admin completes wizard and clicks "Finish Setup"
2. One or more API calls fail (e.g., compliance framework activation)
3. System shows error toast: "Some settings couldn't be saved. Please review in Settings."
4. Onboarding is still marked as completed (partial config is better than re-showing wizard)
5. Admin can fix remaining settings manually

## User Impact

| Role | Impact |
|------|--------|
| **Admin** | Primary user. Sees onboarding wizard on first login. Controls module visibility for the whole company. |
| **Technician** | Indirect. Sees a cleaner sidebar based on admin's module selection. No onboarding wizard. |
| **Employee** | Indirect. Sees fewer, more relevant options. No onboarding wizard. |
| **Super Admin** | No impact. Super admins always see everything. No onboarding wizard. |

## Scope

### Included
- 3-step onboarding wizard (sector -> frameworks -> modules)
- New `sector` field on Company entity
- New `onboarding_completed_at` field on Company entity
- Sector-to-framework recommendation mapping
- Module-to-nav-paths mapping for hide/show
- Skip option
- Summary step with confirmation
- i18n (EN/ES) for all wizard text
- Sector field visible and editable in Company Settings page
- "Re-run setup wizard" button in Company Settings page

### Excluded
- Per-user onboarding (this is company-level, first admin only)
- Guided tours / tooltips within modules (separate feature)
- Module-level permissions (hiding nav items != revoking access to API endpoints)
- Custom sectors (predefined list only, "Other" as catch-all)
- Analytics tracking of onboarding completion rates (future)
- Onboarding for super admins or employees

## Business Rules

1. Onboarding wizard triggers ONLY for the first admin login when `onboarding_completed_at` is null on the company
2. "Service Desk" module cannot be deactivated -- it is the core product
3. Sector selection does not auto-enable frameworks; it pre-selects them as recommendations. Admin confirms.
4. Module deactivation uses the existing `hidden_nav_items` mechanism (hides sidebar entries, does NOT disable API endpoints)
5. Changing sector later does NOT auto-change frameworks or module visibility -- it only shows a suggestion
6. Skip marks onboarding as completed to prevent re-triggering
7. If a second admin exists, they do NOT see the wizard (company already onboarded)
8. The sector-to-framework mapping is hardcoded (not admin-configurable)
9. Module definitions and their nav path mappings are hardcoded in the frontend
10. Wizard always shows all 3 steps, even if sector was pre-set by Super Admin or a previous run
11. Compliance framework activation reuses the same frontend seeding logic as `ComplianceControlsPage.tsx`
12. SLA nav items (`/sla/policies`, `/sla/dashboard`) belong to the Service Desk module (always visible)
13. Billing (`/billing`) and Reports (`/reports`) are always visible for admin, not tied to any module
14. Admin can re-run the wizard from Company Settings at any time

## Acceptance Criteria

- [ ] Admin's first login shows the onboarding wizard
- [ ] Wizard has 3 steps: Sector, Frameworks, Modules
- [ ] Sector selection saves to Company entity
- [ ] Framework recommendations are based on sector mapping
- [ ] Selected frameworks are enabled via existing compliance controls API
- [ ] Module deactivation hides nav items via existing nav visibility API
- [ ] "Service Desk" is always on and cannot be toggled off
- [ ] Skip option prevents wizard from reappearing without changing any settings
- [ ] Subsequent logins (same or other admins) do not show wizard
- [ ] All text is internationalized (EN/ES)
- [ ] Multi-tenant isolation: each company has independent onboarding state
- [ ] Wizard works on mobile viewport (responsive)
- [ ] "Re-run setup wizard" button in Company Settings opens the wizard with current values pre-filled
- [ ] SLA items are part of Service Desk module (always visible)
- [ ] Billing and Reports remain visible regardless of module selection

## Collateral Impact

| Component | Impact | Action Required |
|-----------|--------|-----------------|
| Company entity | New fields: `sector`, `onboarding_completed_at` | Migration + entity update |
| Company Settings page | Show/edit sector field | Add sector dropdown to existing page |
| Nav visibility API | Called during onboarding | No changes -- existing API reused |
| Compliance controls API | Called during onboarding | No changes -- existing API reused |
| Login/auth flow | Must check onboarding status after login | Minor frontend routing change |
| Sidebar | No changes needed | Already respects `hidden_nav_items` |

## Dependencies

- **E1 (Company Management)** -- Company entity must support new fields (Done)
- **E39 (Compliance Dashboard)** -- Compliance framework toggle API exists (Done)
- **Nav Visibility feature** -- `hidden_nav_items` mechanism exists (Done)
- No external dependencies

## Definition of Done

- [ ] All acceptance criteria met
- [ ] Unit tests for new command/query handlers (sector save, onboarding completion)
- [ ] Integration tests for new/modified endpoints
- [ ] Frontend: wizard renders correctly in Chrome, Firefox, Safari
- [ ] Frontend: responsive layout works on mobile
- [ ] i18n: all text in both EN and ES locale files
- [ ] Migration: adds `sector` and `onboarding_completed_at` to companies table
- [ ] Existing nav visibility and compliance APIs continue to work unchanged
- [ ] `make test` and `make test-integration` pass

## Time Constraints

**Deadline:** None (soft priority)
**Type:** Soft
**Reason:** High-impact UX improvement for activation rate, but no external deadline

## Notes for Planner

- **UI pattern**: Full-screen modal wizard (not inline). Similar to setup wizards in Notion, Linear, or Slack. 3 steps with progress indicator.
- **Existing references**: Reuse the nav visibility API (`PUT /api/v1/settings/nav-visibility`) and compliance controls API. No need to build new backend toggle mechanisms.
- **Multi-tenant**: `sector` and `onboarding_completed_at` are per-company fields. The wizard checks the current user's company.
- **i18n**: Both sector labels and all wizard UI text need EN/ES translations.
- **Module mapping**: The mapping from "module name" to "list of nav paths to hide" lives in the frontend only. The backend just receives `hidden_nav_items` as it does today.
- **Routing**: After login, check if company needs onboarding. If yes, redirect to `/onboarding` (or show modal overlay). After completion, redirect to `/dashboard`.
- **No API endpoint changes for nav visibility or compliance**: The wizard is a frontend orchestrator that calls existing APIs in sequence.
- **New backend needed**: Only a small command to save sector + mark onboarding complete on the Company entity, and a query to check onboarding status.
