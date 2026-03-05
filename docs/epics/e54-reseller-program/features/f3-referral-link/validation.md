# Feature Validation Report

**Document:** F3 — Referral Link
**Type:** Feature
**Parent Epic:** [../../requirements.md](../../requirements.md) (E54 — Reseller Program)
**Date:** 2026-03-03
**Status:** Valid

## Epic Reference Check
- [x] Parent epic referenced
- [x] Epic exists and is accessible
- [x] Feature scope aligns with epic slice (F3 in slicing.md)

## Feature-Specific Validation

### Scope Assessment
**Size:** S (Small) — Correct. The feature adds a referral attribution hook to an existing registration flow plus a dashboard UI element.

### Dependencies Verified
- [x] F1 (Portal Foundation) — `Reseller` entity exists with `referral_code` field (auto-generated 8-char alphanumeric)
- [x] F2 (Account Creation) — `ResellerClient` entity exists with `ClientSource.REFERRAL` enum value

### Acceptance Criteria Review
| # | Criterion | Clear | Testable | Notes |
|---|-----------|-------|----------|-------|
| 1 | Dashboard shows referral link with copy button | Yes | Yes | |
| 2 | URL format: `https://{domain}/auth/register?ref={referral_code}` | Yes | Yes | Frontend route — distinct from API endpoint |
| 3 | Registration page sets `dsm_ref` cookie (30-day) | Yes | Yes | |
| 4 | Registration creates ResellerClient with `source=referral` | Yes | Yes | |
| 5 | Only active resellers get attribution | Yes | Yes | |
| 6 | First-wins rule (no re-attribution) | Yes | Yes | |
| 7 | Transparent to prospect (no UX change) | Yes | Yes | |
| 8 | Client list shows source column | Yes | Yes | Already partially done in F2 |
| 9 | Cookie expires after 30 days | Yes | Yes | |
| 10 | Frontend referral link section on dashboard | Yes | Yes | |

### Technical Feasibility

**Verified in codebase:**
- `Reseller.referral_code` — exists, auto-generated on `create()` via `secrets.choice()` (8 chars)
- `ClientSource.REFERRAL` — exists in `src/reseller_bc/client/domain/enums.py`
- `ResellerClient.create()` — accepts `source: ClientSource` parameter
- Registration endpoint — `POST /api/v1/register` in `adapters/http/api/registration/routers.py`
- `CreateCompanyCommand` — currently has no `referral_code` field (needs extension)
- `RegisterCompanyRequest` schema — currently has no `referral_code` field (needs extension)

### Collateral Impact
| Component | Type | Impact | Risk |
|-----------|------|--------|------|
| `adapters/http/api/registration/routers.py` | Modify | Add optional `referral_code` param to registration endpoint | Low — optional field, backward-compatible |
| `RegisterCompanyRequest` schema | Modify | Add optional `referral_code: str` field | Low — optional field |
| `CreateCompanyCommand` | Modify | Add optional `referral_code` field | Low — optional field |
| `CreateCompanyCommandHandler` | Modify | Add post-registration hook to create ResellerClient | Medium — must not break existing flow |
| Frontend registration page | Modify | Read `ref` param, set `dsm_ref` cookie, pass to API | Low |
| Reseller dashboard page | Modify | Add referral link section | Low |

### State/Transition Analysis
No new entities or states. Uses existing:
- `ResellerClient` creation with `source=REFERRAL` (same as manual, different source)
- `Reseller.status` checked (must be `active` for attribution)

### Edge Cases Identified
| Edge Case | Addressed | Notes |
|-----------|-----------|-------|
| Invalid referral code | Yes | "fail silently if code is invalid" |
| Inactive reseller | Yes | AC #5 — only active resellers |
| Company already attributed | Yes | AC #6 — first-wins rule |
| Cookie expired | Yes | AC #9 — no attribution |
| Self-referral (reseller registers own company) | No | Minor — unlikely scenario, not blocking |
| Multiple referral codes (cookie vs param mismatch) | Partially | Param takes precedence per AC #4 wording |

## Observations

1. **Registration endpoint path**: Requirements say `POST /auth/register` but the actual API endpoint is `POST /api/v1/register`. The frontend route `/auth/register` is separate from the API path — this is correct as the `ref` param is on the frontend URL, and the backend receives the referral code from the request body or header.

2. **Cookie handling is frontend-only**: The `dsm_ref` cookie is set by the frontend registration page when the `ref` URL parameter is present. The backend doesn't set/read cookies directly — the frontend reads the cookie and passes the referral code in the API request body. This should be explicit in the design.

3. **Referral code lookup**: The requirements don't specify a dedicated endpoint to resolve a referral code (e.g., `GET /api/v1/reseller/referral/{code}`). The handler will need to look up the reseller by referral_code — the `ResellerRepository` may need a `find_by_referral_code()` method.

## Red Flags
None critical.

## Open Questions for Stakeholder
1. Should the `ref` param take precedence over an existing `dsm_ref` cookie, or should the cookie be preserved? (Suggested: param overwrites cookie)
2. Should the reseller be notified when a referral attribution occurs? (Not in current scope, but good for F4 setup)

## Checklist Summary
- Epic Reference: 3/3 passed
- Content Completeness: 10/10 AC are clear and testable
- Collateral Impact: 6 components identified, all manageable
- Technical Feasibility: All dependencies verified in codebase

## Recommendations
1. Add `find_by_referral_code()` to `ResellerRepository` — needed for the attribution lookup
2. Make the cookie-vs-body flow explicit in the design document — frontend sets cookie, reads it on submit, passes code in request body
3. Consider adding a `referral_code` query on the reseller dashboard API to return the formatted URL (avoids hardcoding domain in frontend)
