# Requirement Validation Report

**Document:** docs/epics/e35-mcp-server/requirements.md
**Type:** Epic
**Date:** 2026-02-17
**Status:** Valid (Minor Gaps)

## Summary

Strong requirement document. The epic is well-scoped as a pure adapter layer that reuses 100% of existing business logic. The tool catalog is exhaustive (57 tools mapped 1:1 to endpoints), the data model is clean, the project structure follows DDD conventions, and the Definition of Done is concrete. A few minor gaps noted below — none are blockers.

---

## Business Alignment Assessment

**Primary Objective:** Product differentiation / Developer experience
**Contribution:** Clear — enables AI-native access to the entire platform
**KPIs Defined:** Yes (5 measurable KPIs)
**Justification Type:** Objective with technical rationale

### Justification Quality

| Criteria | Status | Issue |
|----------|--------|-------|
| Specific numbers | Yes | 57 endpoints, 60 tools, 4 roles, 2 transports |
| Evidence sources | Partial | MCP adoption cited as "open standard" but no market data |
| Revenue impact | No | Not applicable — this is a demo/portfolio project |
| Customer names/tickets | N/A | Portfolio project, no external customers |

### Experimentation Assessment

**Is this an experiment?** No — it's a defined feature with clear scope.

**RED FLAGS:**
- [ ] Subjective justification detected — **No**, justification is technical and specific
- [ ] Missing revenue/cost impact — **N/A** (portfolio project)
- [ ] No evidence provided — **No**, MCP SDK and protocol are real, well-documented
- [x] KPIs are technical metrics, not business metrics — acceptable for this project type

---

## Entities Identified

| Entity | CRUD Coverage | States Defined | Delete Strategy |
|--------|---------------|----------------|-----------------|
| ApiKey | Create, Read (List), Delete (Revoke) | active, revoked (via `is_active`) | Soft delete (is_active=false) |
| MCP Tool | Read (List), Execute (Call) | N/A (stateless) | N/A |

### ApiKey Entity Analysis

**CRUD Check:**
| Operation | Covered | Notes |
|-----------|---------|-------|
| Create | Yes | POST `/api/v1/auth/api-keys` |
| Read (single) | **No** | No GET `/api/v1/auth/api-keys/{key_id}` endpoint |
| Read (list) | Yes | GET `/api/v1/auth/api-keys` |
| Update | **No** | No rename/edit endpoint (e.g., update key name) |
| Delete | Yes | DELETE (revoke) `/api/v1/auth/api-keys/{key_id}` |

**Gap:** No single-key GET or update-name endpoint. Minor — listing is sufficient for most use cases.

### ApiKey State Analysis

| Aspect | Defined | Notes |
|--------|---------|-------|
| Initial status | Yes | `is_active=True` on creation |
| All statuses | Yes | active (true), revoked (false) |
| Transitions | Implicit | active → revoked (via DELETE) |
| Inverse operation | **No** | No reactivation of revoked keys |
| Delete strategy | Yes | Soft delete via `is_active=false` |
| Restore capability | **No** | Cannot un-revoke a key |

**Gap:** No key reactivation. Acceptable — security best practice is to create a new key rather than reactivate a revoked one. Should be documented as intentional.

---

## Missing Use Cases

| Use Case | Reason | Priority | Recommendation |
|----------|--------|----------|----------------|
| API key rate limiting | No mention of rate limits per key | Low | Consider adding later; not needed for v1 |
| API key expiration | Keys have no TTL/expiry | Low | Acceptable for v1; add `expires_at` column later if needed |
| Key rotation | No built-in rotate (revoke old + create new atomically) | Low | Users can do this manually; convenience endpoint is nice-to-have |
| Max keys per user | No limit defined | Medium | Should define a limit (e.g., 10) to prevent abuse |
| Audit log of key usage | `last_used_at` is updated, but no per-call audit log | Low | Existing logging covers this |
| `download_report` tool returns binary | How does MCP return a PDF file? | Medium | Needs clarification — return signed URL instead of binary content |
| `import_assets` tool receives CSV as string | Large CSVs could be problematic | Low | Document size limits; existing 1MB limit from HTTP applies |
| Registration endpoint not included | `POST /api/v1/registration` is not in tool catalog | Low | Intentional — company registration is not an AI operation |
| Health check not included | `GET /api/v1/health` not in tool catalog | Low | Correct — not useful as an MCP tool |

---

## Missing State Information

| Entity | Missing Info | Recommendation |
|--------|--------------|----------------|
| ApiKey | Max keys per user | Add a limit (5-10) to prevent abuse |
| ApiKey | No `expires_at` column | Not a blocker, but mention it's intentionally omitted for v1 |
| MCP Server | Graceful shutdown behavior | What happens to in-flight tool calls on server restart? |

---

## Collateral Impact

| Component | Type | Impact | Action Required |
|-----------|------|--------|-----------------|
| `alembic/` | Migration | New table | Create migration |
| `adapters/http/api/auth/` | New endpoints | 3 API key endpoints | Add to existing auth router |
| `adapters/mcp/` | New module | Entire MCP adapter | Create from scratch |
| `src/mcp_bc/` | New BC | API key domain | Create from scratch |
| `app.py` | Modification | Mount MCP SSE | Small addition |
| `pyproject.toml` | Dependency | `mcp` SDK | Add package |
| `core/config.py` | Modification | New MCP settings | Add config fields |
| `.env.example` | Modification | MCP config vars | Update |
| `tests/` | New tests | Full test suite for MCP | Create |
| `Makefile` | **Not mentioned** | May need `make mcp` command | Add convenience command |
| `docker-compose.yml` | **Not mentioned** | No changes needed (MCP runs in same process) | Verify |
| `web/app/` | **Not mentioned** | API key management UI? | Clarify: CLI-only or frontend page? |
| Existing code | None | Zero changes | Verified |

**Gap:** No mention of frontend UI for API key management. Admins need to create/revoke keys — will this be API-only (via curl/MCP) or should a frontend page exist?

---

## Slicing Assessment

**Size:** Large (new BC + new adapter + 60 tools + migration + tests)
**Slicing needed:** Yes
**Recommended slices:**

| Feature | Scope | Dependencies |
|---------|-------|-------------|
| F0: API Key BC | Entity, repo, migration, CRUD endpoints | None |
| F1: MCP Server Core | Server setup, auth, stdio transport | F0 |
| F2: Asset + Request Tools | 20 tools (highest value) | F1 |
| F3: User + Department + Company Tools | 17 tools | F1 |
| F4: Dashboard + Report + My Tools | 18 tools | F1 |
| F5: Auth Tools + API Key MCP Tools | 5 tools | F1, F0 |
| F6: SSE Transport | Mount in FastAPI, production-ready | F1 |
| F7: Role Filtering | Dynamic tool list per role | F1 |

**Out of scope dependencies:**
| Item | Info Needed Now | Why |
|------|-----------------|-----|
| MCP SDK API stability | Version to pin | SDK is relatively new; pin exact version |
| Claude Desktop MCP config format | How to register DSM server | Needed for compatibility test |

---

## Time Constraints Assessment

**Deadline:** Not specified
**Type:** None
**Reason:** N/A
**Realistic:** Yes — well-scoped, no unknowns in business logic (all handlers exist)
**Calendar conflicts:** None
**Buffer included:** N/A

### Deadline Risk Analysis

No deadline defined. This is appropriate for a portfolio project feature.

---

## Testing Assessment

**Tests defined:** Yes
| Test Type | Required | Defined | Gap |
|-----------|----------|---------|-----|
| Unit | Yes | Yes | API key BC + tool registration |
| Integration | Yes | Yes | E2E MCP flow + isolation + role enforcement |
| Compatibility | Yes | Yes | Claude Desktop + Cursor |
| E2E | Optional | No | Not needed if integration tests cover MCP protocol |
| Performance | Optional | Partially | Latency KPI defined but no test methodology |

**Critical scenarios identified:** Yes — multi-tenant isolation, role filtering, revoked key rejection
**Test data requirements:** Existing seed data sufficient (3 companies, multiple roles)

---

## Definition of Done Assessment

**DoD defined:** Yes (15 criteria)

| Criteria | Defined | Clear |
|----------|---------|-------|
| Acceptance criteria | Yes | 15 checkboxes, all measurable |
| Quality gates | Yes | `make test` + `make lint` |
| Sign-off process | No | Not defined (acceptable for solo project) |
| Training needs | No | README update mentioned |

---

## Red Flags

- [ ] **None critical** — No blockers found
- [x] **Minor:** `download_report` tool behavior unclear for binary content (return signed URL?)
- [x] **Minor:** No max API keys per user limit defined
- [x] **Minor:** No frontend UI mentioned for API key management
- [x] **Minor:** `update_my_company_settings` minimum role should be Admin, not Employee (currently in "My Tools" section with Employee min role)

---

## Open Questions for Stakeholder

1. **`download_report` tool:** Should it return the signed URL (string) or attempt to return binary content? Signed URL is recommended since MCP tool responses are JSON.
2. **API key management UI:** Will there be a frontend page for admins to create/manage API keys, or is it API-only for now?
3. **Max keys per user:** What's the limit? Recommend 10.
4. **`update_my_company_settings` role:** The requirement puts it in "My Tools (Employee)" but only Admins can update company settings. Is this intentional?
5. **MCP SDK version:** Which version of the `mcp` Python package should we pin? The SDK is evolving.

---

## Checklist Summary

### Business Alignment: 4/5 passed
- [x] Objective defined
- [x] Contribution explained
- [x] KPIs defined (technical)
- [x] No subjective justification
- [ ] Market/revenue data (N/A for portfolio)

### Content Completeness: 9/10 passed
- [x] Problem statement
- [x] Current vs target state
- [x] Architecture diagram
- [x] Tool catalog (exhaustive)
- [x] Data model
- [x] Project structure
- [x] Transport modes
- [x] Authentication design
- [x] Role filtering
- [ ] Binary response handling (download_report)

### Entity & Operations: 5/6 passed
- [x] ApiKey entity defined
- [x] Create / List / Delete covered
- [x] States defined (active/revoked)
- [x] Key format specified
- [x] Hash-only storage
- [ ] Max keys per user not defined

### Use Case Coverage: 8/9 passed
- [x] All 57 API endpoints mapped
- [x] Role-based filtering
- [x] Multi-tenant isolation
- [x] Dual transport (SSE + stdio)
- [x] JWT passthrough
- [x] Error mapping
- [x] Logging
- [x] Idempotency
- [ ] Binary file handling (reports)

### Collateral Impact: 8/9 passed
- [x] Migration identified
- [x] New endpoints identified
- [x] New adapter identified
- [x] New BC identified
- [x] app.py changes identified
- [x] Dependencies identified
- [x] Config changes identified
- [x] Existing code: zero changes
- [ ] Frontend UI for key management not addressed

### Slicing: Not done yet (recommended)

### Time Constraints: N/A (no deadline)

### Testing: 4/5 passed
- [x] Unit tests defined
- [x] Integration tests defined
- [x] Compatibility tests defined
- [x] Critical scenarios identified
- [ ] Performance test methodology not specified

### Definition of Done: 5/5 passed
- [x] Criteria defined (15)
- [x] All criteria measurable
- [x] Quality gates included
- [x] Documentation included
- [x] Zero-regression guarantee included

---

## Recommendations

1. **Clarify `download_report` tool** — Return signed URL string, not binary. Add a note to the tool catalog.
2. **Add max API keys per user** — Recommend 10. Add validation in create command.
3. **Clarify `update_my_company_settings` role** — Fix the min role to Admin in the My Tools table.
4. **Run requirement slicing** — The epic is large enough to benefit from formal slicing into 7-8 features for incremental delivery.
5. **Pin MCP SDK version** — Check latest stable version and pin in `pyproject.toml`.
6. **Decide on frontend UI** — If API-only for now, document that. If frontend needed, add it as a separate feature.

**Overall: Strong requirement, ready for slicing and implementation after addressing the 4 minor questions above.**
