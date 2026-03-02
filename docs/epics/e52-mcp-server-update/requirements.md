# Epic E52 — MCP Server Update: Full API Coverage

**Date:** 2026-03-01
**Priority:** High
**Status:** Pending
**Bounded Context:** `mcp_bc` (existing) + `adapters/mcp/tools/` (existing)
**Dependencies:** E35 (MCP Server) — Done, all post-E35 epics that added API endpoints

---

## Business Alignment

### Objective

Update the MCP server to cover **all** API endpoints added since E35 was implemented. The original E35 shipped 60 tools covering the core platform (assets, requests, users, companies, departments, dashboard, reports, my, auth). Since then, ~15 epics have been implemented adding ~120+ new API endpoints across 17 domains — none of which have MCP tools.

An AI assistant connecting via MCP today can manage assets and requests, but cannot:
- Search the knowledge base or manage articles
- Handle security incidents, vulnerabilities, or risks
- Manage SLA policies or check SLA status on requests
- Execute change management workflows
- Manage asset checkout/custody lifecycle
- Access procurement, vendors, maintenance, shipping, or scheduling
- Query the new dashboard endpoints (budget, shipments, maintenance, checkouts)
- Use custom fields, workflow templates, or audit/compliance features

This gap makes the MCP server significantly less useful than the web UI for AI-driven IT operations.

### KPI Targets

| KPI | Target |
|-----|--------|
| API coverage | 100% of public API endpoints exposed as MCP tools |
| New tools | ~120 new tools (from 60 → ~180 total) |
| Zero regressions | All existing 60 tools continue working unchanged |
| Same patterns | New tools follow identical patterns as E35 (registry, role filter, error mapping) |

### Evidence

- AI-assisted IT operations is the primary differentiator for DSM Control vs competitors
- Customers using Claude Desktop / Cursor expect to manage all platform features via MCP, not just assets and requests
- The MCP tool catalog is visible to AI clients — a comprehensive catalog signals platform maturity
- Every missing tool is a workflow an AI agent cannot automate

---

## Current State

### Existing MCP Tools (60 — from E35)

| Module | Tools | Min Role |
|--------|-------|----------|
| `tools/assets.py` | 10 | Technician |
| `tools/requests.py` | 10 | Employee/Technician |
| `tools/users.py` | 7 | Admin |
| `tools/companies.py` | 5 | Super Admin |
| `tools/departments.py` | 5 | Admin |
| `tools/dashboard.py` | 7 | Admin |
| `tools/reports.py` | 4 | Admin |
| `tools/my.py` | 7 | Employee/Admin |
| `tools/auth.py` | 5 | Employee |

### Architecture (unchanged)

The MCP adapter pattern from E35 remains unchanged:
- Each tool module uses `@registry.tool()` decorator
- Tools call existing command/query handlers — no business logic duplication
- Role-based filtering via `ToolRegistry`
- Auth via API key or JWT bearer token
- SSE + stdio transports

New tools follow the exact same pattern. The only change is adding new tool modules and extending existing ones.

---

## Gap Analysis: New Tools Required

### Phase 1 — High Priority (AI agent effectiveness)

These gaps directly limit what an AI assistant can do when managing IT operations.

#### F1: Knowledge Base Tools (14 tools — new module `tools/kb.py`)

| Tool | Min Role | Endpoint | Description |
|------|----------|----------|-------------|
| `search_kb_articles` | Employee | GET `/api/v1/kb/search` | Full-text search published articles |
| `suggest_kb_articles` | Employee | GET `/api/v1/kb/suggest` | AI-suggest articles by text query |
| `list_kb_articles_public` | Employee | GET `/api/v1/kb/public` | List published articles for employees |
| `list_kb_articles` | Technician | GET `/api/v1/kb/articles` | List all articles (inc. draft/archived) |
| `get_kb_article` | Employee | GET `/api/v1/kb/articles/{id}` | Get article detail |
| `create_kb_article` | Technician | POST `/api/v1/kb/articles` | Create article (draft) |
| `update_kb_article` | Technician | PUT `/api/v1/kb/articles/{id}` | Update article content |
| `publish_kb_article` | Technician | POST `/api/v1/kb/articles/{id}/publish` | Publish article |
| `unpublish_kb_article` | Technician | POST `/api/v1/kb/articles/{id}/unpublish` | Unpublish article |
| `archive_kb_article` | Technician | POST `/api/v1/kb/articles/{id}/archive` | Archive article |
| `delete_kb_article` | Admin | DELETE `/api/v1/kb/articles/{id}` | Delete article |
| `list_kb_categories` | Employee | GET `/api/v1/kb/categories` | List categories |
| `create_kb_category` | Admin | POST `/api/v1/kb/categories` | Create category |
| `update_kb_category` | Admin | PUT `/api/v1/kb/categories/{id}` | Update category |

**Why high priority:** An AI assistant that can search and suggest KB articles can deflect tickets and provide instant answers — the highest-value AI use case.

#### F2: Security Incident Tools (12 tools — new module `tools/incidents.py`)

| Tool | Min Role | Endpoint | Description |
|------|----------|----------|-------------|
| `create_incident` | Technician | POST `/api/v1/incidents` | Create security incident |
| `list_incidents` | Technician | GET `/api/v1/incidents` | List incidents with filters |
| `get_incident` | Technician | GET `/api/v1/incidents/{id}` | Get incident detail |
| `update_incident` | Technician | PUT `/api/v1/incidents/{id}` | Update incident |
| `change_incident_status` | Technician | PATCH `/api/v1/incidents/{id}/status` | Change status |
| `change_incident_severity` | Technician | PATCH `/api/v1/incidents/{id}/severity` | Change severity |
| `assign_incident` | Technician | PATCH `/api/v1/incidents/{id}/assign` | Assign to technician |
| `link_asset_to_incident` | Technician | POST `/api/v1/incidents/{id}/assets` | Link affected asset |
| `get_incident_dashboard` | Admin | GET `/api/v1/incidents/dashboard` | Incident dashboard |
| `create_incident_postmortem` | Technician | POST `/api/v1/incidents/{id}/postmortem` | Create post-mortem |
| `report_incident` | Employee | POST `/api/v1/my/report-incident` | Employee reports security incident |
| `my_incidents` | Employee | GET `/api/v1/my/incidents` | My reported incidents |

**Why high priority:** NIS2/DORA incident response is a core compliance requirement. AI agents must be able to create, triage, and escalate incidents.

#### F3: SLA Management Tools (7 tools — new module `tools/sla.py`)

| Tool | Min Role | Endpoint | Description |
|------|----------|----------|-------------|
| `create_sla_policy` | Admin | POST `/api/v1/sla/policies` | Create SLA policy |
| `list_sla_policies` | Admin | GET `/api/v1/sla/policies` | List SLA policies |
| `get_sla_policy` | Admin | GET `/api/v1/sla/policies/{id}` | Get policy detail |
| `update_sla_policy` | Admin | PUT `/api/v1/sla/policies/{id}` | Update SLA policy |
| `deactivate_sla_policy` | Admin | DELETE `/api/v1/sla/policies/{id}` | Deactivate policy |
| `get_request_sla_status` | Technician | GET `/api/v1/sla/requests/{id}/status` | Get SLA status for a request |
| `get_sla_dashboard` | Admin | GET `/api/v1/sla/dashboard` | SLA compliance dashboard |

**Why high priority:** An AI agent managing requests needs SLA context to prioritize correctly.

#### F4: Asset CMDB & Locations (13 tools — extend `tools/assets.py`)

| Tool | Min Role | Endpoint | Description |
|------|----------|----------|-------------|
| `list_asset_locations` | Technician | GET `/api/v1/assets/locations` | List locations |
| `create_asset_location` | Admin | POST `/api/v1/assets/locations` | Create location |
| `update_asset_location` | Admin | PUT `/api/v1/assets/locations/{id}` | Update location |
| `delete_asset_location` | Admin | DELETE `/api/v1/assets/locations/{id}` | Delete location |
| `move_asset` | Technician | PATCH `/api/v1/assets/{id}/move` | Move asset to location |
| `set_asset_criticality` | Technician | PATCH `/api/v1/assets/{id}/criticality` | Set criticality level |
| `update_asset_bia` | Admin | PATCH `/api/v1/assets/{id}/bia` | Update Business Impact Analysis |
| `get_asset_impact` | Technician | GET `/api/v1/assets/{id}/impact` | Get dependency/impact graph |
| `get_cmdb_dashboard` | Admin | GET `/api/v1/assets/cmdb-dashboard` | CMDB dashboard |
| `list_ci_relationships` | Technician | GET `/api/v1/assets/{id}/relationships` | List CI relationships |
| `create_ci_relationship` | Technician | POST `/api/v1/assets/{id}/relationships` | Create CI relationship |
| `update_ci_relationship` | Technician | PUT `/api/v1/assets/{id}/relationships/{rid}` | Update CI relationship |
| `delete_ci_relationship` | Technician | DELETE `/api/v1/assets/{id}/relationships/{rid}` | Delete CI relationship |

Also update existing `list_assets` tool to add `location_id` and `criticality` filter parameters.

**Why high priority:** Asset management is the most-used domain and CMDB features are critical for compliance.

#### F5: Request Sub-features (5 tools — extend `tools/requests.py`)

| Tool | Min Role | Endpoint | Description |
|------|----------|----------|-------------|
| `set_affected_assets` | Technician | PATCH `/api/v1/requests/{id}/affected-assets` | Link assets to request |
| `list_request_events` | Technician | GET `/api/v1/requests/{id}/events` | Get request event timeline |
| `get_request_checklist` | Technician | GET `/api/v1/requests/{id}/checklist` | Get request checklist |
| `toggle_checklist_item` | Technician | PATCH checklist item endpoint | Toggle checklist item done/undone |
| `get_request_sla_status` | Technician | GET `/api/v1/sla/requests/{id}/status` | Get SLA status (alias in requests context) |

### Phase 2 — Medium Priority (compliance & operations)

#### F6: Vulnerability Management (8 tools — new module `tools/vulnerabilities.py`)

| Tool | Min Role | Endpoint | Description |
|------|----------|----------|-------------|
| `create_vulnerability` | Technician | POST `/api/v1/vulnerabilities` | Create vulnerability |
| `list_vulnerabilities` | Technician | GET `/api/v1/vulnerabilities` | List with filters |
| `get_vulnerability` | Technician | GET `/api/v1/vulnerabilities/{id}` | Get detail |
| `update_vulnerability` | Technician | PUT `/api/v1/vulnerabilities/{id}` | Update |
| `change_vulnerability_status` | Technician | PATCH `/api/v1/vulnerabilities/{id}/status` | Change status |
| `link_assets_to_vulnerability` | Technician | POST `/api/v1/vulnerabilities/{id}/assets` | Link affected assets |
| `create_remediation_tickets` | Technician | POST `/api/v1/vulnerabilities/{id}/remediation` | Create remediation tickets |
| `get_vulnerability_dashboard` | Admin | GET `/api/v1/vulnerabilities/dashboard` | Dashboard |

#### F7: Change Management (7 tools — new module `tools/changes.py`)

| Tool | Min Role | Endpoint | Description |
|------|----------|----------|-------------|
| `create_change_request` | Technician | POST `/api/v1/changes` | Create change request |
| `list_change_requests` | Technician | GET `/api/v1/changes` | List with filters |
| `get_change_request` | Technician | GET `/api/v1/changes/{id}` | Get detail |
| `approve_change_request` | Admin | PATCH `/api/v1/changes/{id}/approve` | Approve |
| `reject_change_request` | Admin | PATCH `/api/v1/changes/{id}/reject` | Reject |
| `implement_change` | Technician | PATCH `/api/v1/changes/{id}/implement` | Mark as implemented |
| `get_change_dashboard` | Admin | GET `/api/v1/changes/dashboard` | Dashboard |

#### F8: Risk Register (8 tools — new module `tools/risks.py`)

| Tool | Min Role | Endpoint | Description |
|------|----------|----------|-------------|
| `create_risk` | Admin | POST `/api/v1/risks` | Create risk |
| `list_risks` | Admin | GET `/api/v1/risks` | List with filters |
| `get_risk` | Admin | GET `/api/v1/risks/{id}` | Get detail |
| `update_risk` | Admin | PUT `/api/v1/risks/{id}` | Update |
| `delete_risk` | Admin | DELETE `/api/v1/risks/{id}` | Delete |
| `assess_risk` | Admin | PATCH `/api/v1/risks/{id}/assess` | Record assessment |
| `add_risk_mitigation` | Admin | POST `/api/v1/risks/{id}/mitigations` | Add mitigation action |
| `get_risk_dashboard` | Admin | GET `/api/v1/risks/dashboard` | Dashboard |

#### F9: Asset Checkout & Custody (8 tools — new module `tools/checkouts.py`)

| Tool | Min Role | Endpoint | Description |
|------|----------|----------|-------------|
| `create_checkout` | Technician | POST `/api/v1/checkouts` | Create equipment checkout |
| `list_checkouts` | Technician | GET `/api/v1/checkouts` | List company checkouts |
| `get_checkout` | Technician | GET `/api/v1/checkouts/{id}` | Get checkout detail |
| `cancel_checkout` | Technician | PATCH `/api/v1/checkouts/{id}/cancel` | Cancel checkout |
| `checkin_asset` | Technician | PATCH `/api/v1/checkouts/{id}/checkin` | Check in asset |
| `my_custody` | Employee | GET `/api/v1/my/custody` | My current custody |
| `accept_equipment` | Employee | POST `/api/v1/my/equipment/{id}/accept` | Accept custody |
| `my_custody_history` | Employee | GET `/api/v1/my/custody/history` | My custody history |

#### F10: Audit & Compliance (6 tools — new module `tools/audit.py`)

| Tool | Min Role | Endpoint | Description |
|------|----------|----------|-------------|
| `list_audit_entries` | Admin | GET `/api/v1/audit/entries` | List audit trail entries |
| `get_audit_entry` | Admin | GET `/api/v1/audit/entries/{id}` | Get audit entry detail |
| `list_compliance_controls` | Admin | GET `/api/v1/audit/compliance/controls` | List compliance controls |
| `assess_compliance_control` | Admin | PATCH `/api/v1/audit/compliance/controls/{id}/assess` | Record assessment |
| `get_compliance_dashboard` | Admin | GET `/api/v1/audit/compliance/dashboard` | Compliance dashboard |
| `add_compliance_evidence` | Admin | POST `/api/v1/audit/compliance/controls/{id}/evidence` | Upload evidence |

#### F11: Custom Fields (7 tools — new module `tools/custom_fields.py`)

| Tool | Min Role | Endpoint | Description |
|------|----------|----------|-------------|
| `list_custom_field_definitions` | Admin | GET `/api/v1/custom-fields/definitions` | List by entity type |
| `get_custom_field_definition` | Admin | GET `/api/v1/custom-fields/definitions/{id}` | Get definition |
| `create_custom_field_definition` | Admin | POST `/api/v1/custom-fields/definitions` | Create definition |
| `update_custom_field_definition` | Admin | PUT `/api/v1/custom-fields/definitions/{id}` | Update |
| `delete_custom_field_definition` | Admin | DELETE `/api/v1/custom-fields/definitions/{id}` | Delete |
| `activate_custom_field` | Admin | POST `/api/v1/custom-fields/definitions/{id}/activate` | Activate |
| `deactivate_custom_field` | Admin | POST `/api/v1/custom-fields/definitions/{id}/deactivate` | Deactivate |

### Phase 3 — Lower Priority (operational domains)

#### F12: Dashboard Additions (7 tools — extend `tools/dashboard.py`)

| Tool | Min Role | Endpoint | Description |
|------|----------|----------|-------------|
| `dashboard_request_queue_counts` | Technician | GET `/api/v1/dashboard/requests/queue-counts` | Queue counts per technician |
| `dashboard_my_task_counts` | Technician | GET `/api/v1/dashboard/my-tasks/counts` | My aggregate task counts |
| `dashboard_budget_health` | Admin | GET `/api/v1/dashboard/budget-health` | Budget health by department |
| `dashboard_recent_purchase_orders` | Admin | GET `/api/v1/dashboard/recent-purchase-orders` | Recent POs |
| `dashboard_shipment_summary` | Admin | GET `/api/v1/dashboard/shipments/summary` | Shipment summary |
| `dashboard_maintenance_summary` | Admin | GET `/api/v1/dashboard/maintenance` | Maintenance summary |
| `dashboard_checkout_summary` | Admin | GET `/api/v1/dashboard/checkouts` | Checkout summary |

#### F13: My/* Additions (6 tools — extend `tools/my.py`)

| Tool | Min Role | Endpoint | Description |
|------|----------|----------|-------------|
| `update_my_profile` | Employee | PATCH `/api/v1/my/profile` | Update my name |
| `my_appointments` | Employee | GET `/api/v1/my/appointments` | My scheduled appointments |
| `my_shipments` | Employee | GET `/api/v1/my/shipments` | My equipment shipments |
| `my_maintenance` | Technician | GET `/api/v1/my/maintenance` | My maintenance tasks |
| `get_onboarding_status` | Employee | GET `/api/v1/my/onboarding/status` | Onboarding wizard status |
| `complete_onboarding` | Admin | POST `/api/v1/my/onboarding/complete` | Complete onboarding |

#### F14: Company & Billing Additions (5 tools — extend `tools/companies.py`)

| Tool | Min Role | Endpoint | Description |
|------|----------|----------|-------------|
| `get_company_billing` | Super Admin | GET `/api/v1/companies/{id}/billing` | Get billing info |
| `get_company_invoices` | Super Admin | GET `/api/v1/companies/{id}/invoices` | Get invoice history |
| `override_company_plan` | Super Admin | PATCH `/api/v1/companies/{id}/billing/plan` | Override plan |
| `grant_complimentary_plan` | Super Admin | POST `/api/v1/companies/{id}/billing/complimentary` | Grant free plan |
| `revoke_complimentary_plan` | Super Admin | DELETE `/api/v1/companies/{id}/billing/complimentary` | Revoke free plan |

Also update existing `list_companies` tool to add `in_trial` and `plan` filter parameters.

#### F15: Department & User Additions (5 tools — extend existing modules)

Departments (extend `tools/departments.py`):

| Tool | Min Role | Endpoint | Description |
|------|----------|----------|-------------|
| `assign_department_manager` | Admin | PUT `/api/v1/departments/{id}/manager` | Assign manager |
| `remove_department_manager` | Admin | DELETE `/api/v1/departments/{id}/manager` | Remove manager |

Also update existing `update_department` tool to expose `priority_weight` and `budget_enforcement_enabled` parameters.

Users (extend `tools/users.py`):

| Tool | Min Role | Endpoint | Description |
|------|----------|----------|-------------|
| `import_users_preview` | Admin | POST `/api/v1/users/import/preview` | Preview CSV import |
| `import_users_confirm` | Admin | POST `/api/v1/users/import/confirm` | Confirm CSV import |
| `quick_create_employee` | Admin | POST `/api/v1/users/quick-create` | Quick-create without invite |

#### F16: Procurement (8+ tools — new module `tools/procurement.py`)

| Tool | Min Role | Endpoint | Description |
|------|----------|----------|-------------|
| `create_purchase_order` | Admin | POST `/api/v1/purchase-orders` | Create PO |
| `list_purchase_orders` | Admin | GET `/api/v1/purchase-orders` | List POs |
| `get_purchase_order` | Admin | GET `/api/v1/purchase-orders/{id}` | Get PO detail |
| `update_purchase_order` | Admin | PUT `/api/v1/purchase-orders/{id}` | Update PO |
| `approve_purchase_order` | Admin | PATCH PO approve endpoint | Approve PO |
| `list_budgets` | Admin | GET `/api/v1/budgets` | List budgets |
| `get_budget` | Admin | GET `/api/v1/budgets/{id}` | Get budget detail |
| `update_budget` | Admin | PUT `/api/v1/budgets/{id}` | Update budget |

#### F17: Vendor Management (8+ tools — new module `tools/vendors.py`)

| Tool | Min Role | Endpoint | Description |
|------|----------|----------|-------------|
| `create_vendor` | Admin | POST `/api/v1/vendors` | Create vendor |
| `list_vendors` | Admin | GET `/api/v1/vendors` | List vendors |
| `get_vendor` | Admin | GET `/api/v1/vendors/{id}` | Get vendor detail |
| `update_vendor` | Admin | PUT `/api/v1/vendors/{id}` | Update vendor |
| `list_vendor_contracts` | Admin | GET `/api/v1/vendors/{id}/contracts` | List contracts |
| `create_vendor_contract` | Admin | POST `/api/v1/vendors/{id}/contracts` | Create contract |
| `get_vendor_risk_profile` | Admin | GET `/api/v1/vendors/{id}/risk-profile` | Risk profile |
| `get_vendor_dashboard` | Admin | GET `/api/v1/vendors/dashboard` | Vendor dashboard |

#### F18: Maintenance (6+ tools — new module `tools/maintenance.py`)

| Tool | Min Role | Endpoint | Description |
|------|----------|----------|-------------|
| `create_maintenance_record` | Technician | POST `/api/v1/maintenance` | Create record |
| `list_maintenance_records` | Technician | GET `/api/v1/maintenance` | List records |
| `get_maintenance_record` | Technician | GET `/api/v1/maintenance/{id}` | Get detail |
| `update_maintenance_record` | Technician | PUT `/api/v1/maintenance/{id}` | Update |
| `list_maintenance_templates` | Admin | GET `/api/v1/maintenance-templates` | List templates |
| `create_maintenance_template` | Admin | POST `/api/v1/maintenance-templates` | Create template |

#### F19: Shipping & Scheduling (8+ tools — new modules)

Shipping (`tools/shipping.py`):

| Tool | Min Role | Endpoint | Description |
|------|----------|----------|-------------|
| `create_shipment` | Technician | POST `/api/v1/shipments` | Create shipment |
| `list_shipments` | Technician | GET `/api/v1/shipments` | List shipments |
| `get_shipment` | Technician | GET `/api/v1/shipments/{id}` | Get detail |
| `update_shipment_status` | Technician | PATCH `/api/v1/shipments/{id}/status` | Update status |

Scheduling (`tools/appointments.py`):

| Tool | Min Role | Endpoint | Description |
|------|----------|----------|-------------|
| `create_appointment` | Technician | POST `/api/v1/appointments` | Create appointment |
| `list_appointments` | Technician | GET `/api/v1/appointments` | List appointments |
| `get_appointment` | Technician | GET `/api/v1/appointments/{id}` | Get detail |
| `update_appointment` | Technician | PUT `/api/v1/appointments/{id}` | Update |

#### F20: Workflow Templates & Checklists (6+ tools — new module `tools/workflows.py`)

| Tool | Min Role | Endpoint | Description |
|------|----------|----------|-------------|
| `list_workflow_templates` | Admin | GET `/api/v1/workflow-templates` | List templates |
| `get_workflow_template` | Admin | GET `/api/v1/workflow-templates/{id}` | Get template |
| `create_workflow_template` | Admin | POST `/api/v1/workflow-templates` | Create template |
| `update_workflow_template` | Admin | PUT `/api/v1/workflow-templates/{id}` | Update template |
| `delete_workflow_template` | Admin | DELETE `/api/v1/workflow-templates/{id}` | Delete template |
| `generate_checklist` | Technician | POST `/api/v1/checklist/generate` | Generate checklist from template |

---

## Summary

| Phase | Features | New Tools | Scope |
|-------|----------|-----------|-------|
| Phase 1 | F1–F5 | ~51 | KB, Incidents, SLA, CMDB, Requests |
| Phase 2 | F6–F11 | ~44 | Vulnerabilities, Changes, Risks, Checkouts, Audit, Custom Fields |
| Phase 3 | F12–F20 | ~54+ | Dashboard, My, Billing, Depts, Users, Procurement, Vendors, Maintenance, Shipping, Scheduling, Workflows |
| **Total** | **F1–F20** | **~149** | **From 60 → ~209 tools** |

---

## Implementation Approach

### Pattern

Every new tool follows the exact same pattern established in E35:

```python
@registry.tool(
    name="tool_name",
    description="Clear description of what the tool does",
    min_role=Role.TECHNICIAN,  # or EMPLOYEE, ADMIN, SUPER_ADMIN
)
async def tool_name(ctx: ToolContext, param1: str, param2: int = 10) -> dict:
    handler = SomeQueryHandler(repo=get_repo(ctx.db))
    result = handler.handle(SomeQuery(company_id=ctx.company_id, ...))
    return serialize(result)
```

### New files to create

| File | Features | Tools |
|------|----------|-------|
| `adapters/mcp/tools/kb.py` | F1 | 14 |
| `adapters/mcp/tools/incidents.py` | F2 | 12 |
| `adapters/mcp/tools/sla.py` | F3 | 7 |
| `adapters/mcp/tools/vulnerabilities.py` | F6 | 8 |
| `adapters/mcp/tools/changes.py` | F7 | 7 |
| `adapters/mcp/tools/risks.py` | F8 | 8 |
| `adapters/mcp/tools/checkouts.py` | F9 | 8 |
| `adapters/mcp/tools/audit.py` | F10 | 6 |
| `adapters/mcp/tools/custom_fields.py` | F11 | 7 |
| `adapters/mcp/tools/procurement.py` | F16 | 8+ |
| `adapters/mcp/tools/vendors.py` | F17 | 8+ |
| `adapters/mcp/tools/maintenance.py` | F18 | 6+ |
| `adapters/mcp/tools/shipping.py` | F19 | 4+ |
| `adapters/mcp/tools/appointments.py` | F19 | 4+ |
| `adapters/mcp/tools/workflows.py` | F20 | 6+ |

### Existing files to extend

| File | Features | New Tools | Changes |
|------|----------|-----------|---------|
| `adapters/mcp/tools/assets.py` | F4 | 13 | Add CMDB/location/BIA tools + update `list_assets` filters |
| `adapters/mcp/tools/requests.py` | F5 | 5 | Add affected-assets, events, checklist tools |
| `adapters/mcp/tools/dashboard.py` | F12 | 7 | Add budget, shipment, maintenance, checkout dashboards |
| `adapters/mcp/tools/my.py` | F13 | 6 | Add appointments, shipments, maintenance, onboarding |
| `adapters/mcp/tools/companies.py` | F14 | 5 | Add billing tools + update `list_companies` filters |
| `adapters/mcp/tools/departments.py` | F15 | 2 | Add manager tools + update `update_department` params |
| `adapters/mcp/tools/users.py` | F15 | 3 | Add import, quick-create |
| `adapters/mcp/tools/__init__.py` | All | — | Import new modules to trigger registration |

---

## Collateral Impact

| Component | Impact | Action Required |
|-----------|--------|-----------------|
| `adapters/mcp/tools/__init__.py` | Import new tool modules | Add imports for ~15 new modules |
| `adapters/mcp/tools/*.py` | New tool files + extensions | Create 15 new files, extend 7 existing |
| `tests/unit/mcp/` | New unit tests per tool module | Create test files per new module |
| `tests/integration/` | Extended MCP integration tests | Verify new tools work end-to-end |
| Existing code | **Zero changes** to domain, application, infrastructure, or HTTP layers | None |

---

## Testing Requirements

### Per Feature

Each feature (F1–F20) requires:
- Unit tests for each new tool (parameter validation, handler delegation, response serialization)
- Integration test for at least one representative tool per module (end-to-end via MCP client)
- Role-based access verification (tool only visible/callable by authorized roles)

### Regression

- All existing 60 tools must continue passing their tests unchanged
- `make test` must pass after each feature addition

---

## Definition of Done

### Per Feature
- [ ] All tools for the feature registered and functional
- [ ] Unit tests for each tool
- [ ] Integration test for the module
- [ ] Role filtering verified
- [ ] `adapters/mcp/tools/__init__.py` updated
- [ ] `make test` passes

### Epic-level
- [ ] All 20 features (F1–F20) implemented
- [ ] Total tool count reaches ~209 (verified via tool count assertion)
- [ ] All existing 60 tools unchanged and passing
- [ ] `make test` and `make lint` pass
- [ ] Tested with Claude Desktop or Cursor (representative tools from each phase)
- [ ] E35 requirements.md tool catalog updated to reflect new total

---

## Resolved Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| New epic vs extend E35 | New epic (E52) | E35 is marked Done with its original scope. A new epic makes progress tracking clearer |
| Architecture changes | None — same adapter pattern | E35's pattern works perfectly. No reason to change registry, auth, or transport |
| Phased rollout | 3 phases by priority | Phase 1 (AI effectiveness) delivers the most value first. Phases 2-3 can be done incrementally |
| Auth login tools | Excluded | Magic link, OAuth flows are session-based — not useful for MCP tool calls |
| Billing tools for non-super-admin | Excluded | Stripe billing management is super-admin only — not exposed to regular API key users |
| Registration endpoint | Excluded | Company self-registration is a one-time flow — not useful as MCP tool |

---

## Open Questions

1. **Tool count limit:** Some MCP clients may have limits on advertised tools. With ~209 tools, should we offer a "lite" mode that only registers core tools? — monitor client behavior first
2. **Bulk operations:** Should procurement/vendor tools support batch operations, or stick to one-at-a-time like existing tools? — start with single operations, add bulk later if needed
3. **File upload tools:** Custom fields and compliance evidence have file upload endpoints. MCP tool calls with binary data need special handling (base64 or URL reference). Defer file uploads to follow-up if complex
