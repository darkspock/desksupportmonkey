# Tasks: F1 — Mitigations & Links

**Feature:** [requirements.md](../../requirements.md)
**Design:** [../../design.md](../../design.md)
**Date:** 2026-02-23

## Summary

| # | Task | Complexity | Phase | Status |
|---|------|-----------|-------|--------|
| 1 | Commands: AddMitigation, UpdateMitigation, DeleteMitigation | S | App | Done (F0) |
| 2 | Commands: AddLink, RemoveLink | S | App | Done (F0) |
| 3 | HTTP: Mitigation + Link schemas | S | HTTP | Done (F0) |
| 4 | HTTP: Mitigation + Link router endpoints | M | HTTP | Done (F0) |
| 5 | Frontend: Mitigation + Link sections in RiskDetailPage | M | FE | Done (F0) |
| 6 | Integration tests: Mitigations + Links | M | Test | Done (F0) |
| 7 | i18n: Mitigation + Link translations | S | FE | Done (F0) |

## Notes

All F1 tasks were implemented alongside F0 to keep the router and detail page compilable. The commands, endpoints, frontend sections, tests, and translations are fully complete.

## Detailed Tasks

### Task 1: Mitigation Commands
- **Files:** `src/risk_bc/risk/application/commands/add_mitigation.py`, `update_mitigation.py`, `delete_mitigation.py`
- **What:** AddMitigationCommand (description, owner_id?, target_date?), UpdateMitigationCommand (description?, status?, owner_id?, target_date?), DeleteMitigationCommand. History events recorded.
- [x] Done

### Task 2: Link Commands
- **Files:** `src/risk_bc/risk/application/commands/add_link.py`, `remove_link.py`
- **What:** AddLinkCommand (link_type, link_id) with duplicate check. RemoveLinkCommand. History events recorded.
- [x] Done

### Task 3: Schemas
- **File:** `adapters/http/api/risks/schemas.py`
- **What:** AddMitigationRequest, UpdateMitigationRequest, AddLinkRequest, MitigationResponse, RiskLinkResponse.
- [x] Done

### Task 4: Router endpoints
- **File:** `adapters/http/api/risks/routers.py`
- **What:** POST/PUT/DELETE mitigations, POST/DELETE links with auth and error handling.
- [x] Done

### Task 5: Frontend sections
- **File:** `web/app/src/pages/technician/RiskDetailPage.tsx`
- **What:** Mitigations section with add form, status badges. Links section with type selector and entity ID input.
- [x] Done

### Task 6: Integration tests
- **File:** `tests/integration/test_risks_endpoints.py`
- **What:** TestRiskMitigations (4 tests), TestRiskLinks (4 tests) including duplicate link detection.
- [x] Done

### Task 7: i18n translations
- **Files:** `web/app/src/locales/en.ts`, `es.ts`
- **What:** All mitigation_status, link_type, and page.risks mitigation/link keys.
- [x] Done
