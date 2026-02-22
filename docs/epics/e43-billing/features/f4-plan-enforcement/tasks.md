# Tasks: F4 - Plan Enforcement

**Epic:** [slicing.md](../../slicing.md)
**Depends on:** [F3](../f3-admin-billing-ui/tasks.md)
**Date:** 2026-02-22

---

## Phase 1: Enforcement Guards

### T1.1: require_write_access dependency
- [ ] **File:** `adapters/http/billing_guards.py` (NEW)
- `async def require_write_access(company=Depends(get_current_company), ...) -> None`
  - Calls `PlanGate.is_write_allowed(company.billing_status, settings.OPEN_SOURCE_MODE)`
  - If `billing_status == SUSPENDED`: raise `HTTPException(402, detail="account_suspended")`
  - If `billing_status == OVER_LIMIT`: raise `HTTPException(402, detail="account_read_only")`
- Note: `get_current_company` fetches the Company entity for the authenticated user's company_id

### T1.2: require_feature factory
- [ ] **File:** `adapters/http/billing_guards.py` (same file)
- `def require_feature(feature_key: str) -> Callable`
  - Returns FastAPI dependency: checks `PlanGate.is_feature_available(..., feature_key)`
  - If not available: `HTTPException(402, detail="feature_not_available_on_plan")`

### T1.3: require_user_limit_not_reached dependency
- [ ] **File:** `adapters/http/billing_guards.py` (same file)
- Gets `limit = PlanGate.get_user_limit(company.plan)`
- If None or `open_source_mode` or `complimentary`: return (unlimited)
- Counts active users for company via repository
- If `count >= limit`: `HTTPException(402, detail="plan_limit_reached")`

### T1.4: require_asset_limit_not_reached dependency
- [ ] **File:** `adapters/http/billing_guards.py` (same file)
- Same pattern as T1.3 but for assets: `PlanGate.get_asset_limit(company.plan)`

---

## Phase 2: Endpoint Updates (additive only)

### T2.1: Users router — invite/create
- [ ] **File:** `adapters/http/api/users/routers.py` (MODIFY)
- Add to invite/create endpoint:
  - `Depends(require_user_limit_not_reached)`
  - `Depends(require_write_access)`

### T2.2: Assets router — create
- [ ] **File:** `adapters/http/api/assets/routers.py` (MODIFY)
- Add to `POST /api/v1/assets`:
  - `Depends(require_asset_limit_not_reached)`
  - `Depends(require_write_access)`

### T2.3: All write endpoints — require_write_access
- [ ] Add `Depends(require_write_access)` to all non-GET endpoints:
  - `adapters/http/api/assets/routers.py` — PUT, DELETE, PATCH
  - `adapters/http/api/users/routers.py` — PUT, DELETE, PATCH
  - `adapters/http/api/departments/routers.py` — POST, PUT, DELETE
  - `adapters/http/api/service_requests/routers.py` — POST, PUT, PATCH, DELETE
  - Any other write endpoints present in the codebase at implementation time
- Do NOT add to: GET endpoints, webhook endpoint, auth endpoints, super_admin-only endpoints

### T2.4: Feature-gated endpoints — require_feature
- [ ] Add `Depends(require_feature("feature_key"))` to relevant endpoints that exist in the codebase:
  - Reports → `require_feature("reports")`
  - API keys → `require_feature("api_keys")`
  - AI classification → `require_feature("ai_classification")`
  - Appointments → `require_feature("appointments")`
  - Shipments → `require_feature("shipments")`
  - Maintenance → `require_feature("maintenance")`
  - Procurement → `require_feature("procurement")`
  - MCP server → `require_feature("mcp_server")`
  - SSO → `require_feature("sso")`
  - Audit Trail → `require_feature("audit_trail")`
  - Custom Fields → `require_feature("custom_fields")`
  - Automations → `require_feature("automations")`
  - SLA → `require_feature("sla")`
  - Knowledge Base → `require_feature("knowledge_base")`
  - Onboarding → `require_feature("onboarding")`

---

## Phase 3: Tests

### T3.1: Unit tests — all enforcement guards
- [ ] **File:** `tests/unit/adapters/http/test_billing_guards.py` (NEW)
- Test `require_write_access`: active → pass, suspended → 402 "account_suspended", over_limit → 402 "account_read_only", open_source bypass
- Test `require_feature`: available → pass, not available → 402 "feature_not_available_on_plan", complimentary Enterprise bypass, open_source bypass
- Test `require_user_limit_not_reached`: under limit → pass, at limit → 402 "plan_limit_reached", unlimited plan → pass, complimentary → pass
- Test `require_asset_limit_not_reached`: same pattern

### T3.2: Integration tests — 402 responses
- [ ] **File:** `tests/integration/test_billing_enforcement.py` (NEW)
- Test: invite user at user limit → 402 "plan_limit_reached"
- Test: create asset at asset limit → 402 "plan_limit_reached"
- Test: suspended company write → 402 "account_suspended"
- Test: over-limit company write → 402 "account_read_only"
- Test: Free plan accesses premium feature → 402 "feature_not_available_on_plan"
- Test: complimentary Enterprise bypasses all limits
- Test: OPEN_SOURCE_MODE bypasses all limits

---

## Phase 4: Verification

### T4.1: Run linter
- [ ] `make lint`

### T4.2: Run all tests
- [ ] `make test` + `make test-integration`

### T4.3: Regression check
- [ ] All existing integration tests still pass (guards must not break existing test fixtures)
- Ensure test conftest sets company with `billing_status=active` by default

---

## Task Summary

| Phase | Tasks | New Files | Modified Files |
|---|---|---|---|
| 1. Guards | T1.1-T1.4 | 1 new (billing_guards.py) | — |
| 2. Endpoints | T2.1-T2.4 | — | Multiple routers (additive only) |
| 3. Tests | T3.1-T3.2 | 2 new | — |
| 4. Verification | T4.1-T4.3 | — | — |
