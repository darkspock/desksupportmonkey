# Requirement Validation Report

**Document:** E29: Audit Trail & Compliance Evidence
**Date:** 2026-02-23
**Status:** Needs Revision (minor gaps)

## Summary

The requirement is well-structured with strong business alignment, clear entities, comprehensive use cases, and detailed acceptance criteria. The main gaps are: (1) missing CRUD coverage for ComplianceTag entity, (2) incomplete inverse operation analysis for GDPR anonymization, (3) a transactional concern with the middleware approach for hash chain computation, and (4) missing consideration of MCP tool calls as write operations. Overall quality is high — issues are addressable without major restructuring.

## Business Alignment Assessment

**Primary Objective:** Revenue & Churn
**Contribution:** Clear — Enterprise-tier differentiator for NIS2/DORA/ISO regulated SMBs
**KPIs Defined:** Yes — 5 measurable targets
**Justification Type:** Objective with regulatory evidence

### Justification Quality

| Criteria | Status | Issue |
|----------|--------|-------|
| Specific numbers | Partial | No customer count or revenue projection; regulatory citations are strong but no "X customers asked for this" |
| Evidence sources | Yes | NIS2 Article 21, DORA Article 12, ISO 27001 A.8.15 — all verifiable |
| Revenue impact | Partial | Described as Enterprise upgrade driver but no conversion rate target |
| Customer names/tickets | No | No specific customer requests cited |

**RED FLAGS:**
- [ ] ~~Subjective justification detected~~ — No, regulatory evidence is objective
- [x] Missing revenue/cost impact — No projected conversion rate or ARR impact from Enterprise upgrades
- [ ] ~~No evidence provided~~ — Regulatory evidence is strong
- [ ] ~~Experiment without success metrics~~ — Not an experiment

**Assessment:** Business alignment is solid for a compliance-driven feature. The regulatory evidence is compelling. Revenue impact could be strengthened with Enterprise conversion targets, but this is not blocking.

---

## Entities Identified

| Entity | CRUD Coverage | States Defined | Delete Strategy |
|--------|---------------|----------------|-----------------|
| AuditEntry | Create (auto), Read, List — **No Update, No Delete** | N/A (immutable) | Retention purge only |
| ComplianceTag | **Incomplete** — Add exists, but no Remove/List standalone | N/A | Cascade on entry purge |
| GdprRequest | Create, Read, List — No Update, No Delete | pending → processing → completed/failed | Soft delete (mentioned but not detailed) |
| RetentionPolicy | Create (implicit), Read, Update — No Delete | N/A (config) | Reset to default |

### Missing CRUD Operations

| Entity | Missing Op | Priority | Recommendation |
|--------|-----------|----------|----------------|
| ComplianceTag | Remove tag from entry | High | Admin must be able to untag entries (mistakes happen). Add `DELETE /api/v1/audit/tag` or include remove in PATCH |
| ComplianceTag | List available tags | Medium | Need `GET /api/v1/audit/tags` to populate the tag picker UI. Where does the predefined catalog live? |
| ComplianceTag | Custom tag creation | Low | Open question #5 mentions admins can "extend" — needs a `POST /api/v1/audit/tags` endpoint |
| GdprRequest | Cancel pending request | Medium | What if admin requests anonymization by mistake? Can they cancel before processing starts? |
| RetentionPolicy | Delete/reset | Low | Mentioned "reset to default on delete" but no endpoint. Acceptable as implicit (PUT with default value) |

---

## Missing State Information

| Entity | Missing Info | Question |
|--------|--------------|----------|
| AuditEntry | Compliance tags are mutable on an otherwise immutable entity — is this a contradiction? | Should tagging create a separate `audit_entry_tags` join table instead of mutating the entry's JSON? This preserves true immutability |
| GdprRequest | No `cancelled` state | Can a pending GDPR request be cancelled? If so, add `pending → cancelled` transition |
| GdprRequest | `started_at` field mentioned in state table but not in entity definition | Add `started_at: datetime (nullable)` to GdprRequest entity |
| GdprRequest | Soft delete mentioned but no `deleted_at` or mechanism described | Clarify: is it just status-based filtering or actual soft delete? |

---

## Missing Use Cases

| Use Case | Reason | Priority | Recommendation |
|----------|--------|----------|----------------|
| **UC: Remove compliance tag** | Tags can be added but never removed — no undo | High | Add inverse operation for UC-004 |
| **UC: Cancel GDPR request** | Admin may request anonymization by mistake | Medium | Allow cancellation while status = pending |
| **UC: Retry failed GDPR request** | GDPR request can fail — what then? | Medium | Add retry flow or allow re-creation |
| **UC: View GDPR request detail** | Endpoint exists (GET /gdpr/requests/{id}) but no use case written | Low | Add UC for viewing status, result, error |
| **UC: MCP tool call audit** | MCP write operations (26+ handlers) go through FastAPI but via SSE transport mounted separately | High | Verify middleware intercepts MCP requests. If SSE transport bypasses middleware, need explicit audit capture in MCP handler |
| **UC: Bulk tag entries** | UC-004 implies multi-select + tag but flow is unclear for bulk operations | Low | Clarify: is it one-by-one or batch? PATCH endpoint implies batch |
| **UC: Audit of audit operations** | Who tagged what? Who exported? Who anonymized? These are write operations that should themselves be audited | Medium | Confirm middleware captures audit/gdpr endpoints too (self-referential audit) |
| **UC: Super admin cross-company audit** | Super admin may need to audit across companies for platform-level investigation | Low | Out of scope for E29? Document explicitly |

---

## Collateral Impact

| Component | Type | Impact | Action Required |
|-----------|------|--------|-----------------|
| **All HTTP routers** | Middleware | All write operations captured | Register audit middleware in app.py |
| **MCP SSE transport** | Integration | MCP is mounted via `app.mount()` — middleware may NOT intercept mounted sub-apps | **CRITICAL: Verify BaseHTTPMiddleware applies to mounted apps. If not, need explicit audit in MCP handlers** |
| **Auth dependencies** | Data capture | Need IP + user-agent | Middleware has access to `request.client.host` and `request.headers` — no changes to auth deps needed |
| **User entity** | Schema change | Add `is_anonymized` field | Migration required on `users` table |
| **Celery tasks** | New tasks | 4 new tasks: audit_export, gdpr_export, gdpr_anonymize, retention_purge | Register in `core/tasks/` |
| **Celery Beat** | Scheduling | Retention purge needs periodic schedule | Add to Celery Beat config |
| **MinIO/S3** | Storage | Export files (CSV, PDF, ZIP) | Reuse `S3StorageService` pattern from E6 |
| **Feature gating** | Enforcement | `audit_trail` key already in Enterprise features | Add 402 checks to audit/gdpr endpoints |
| **Notification BC** | Events | Export/anonymization completion notifications | Add 2-3 new EventType values |
| **Sidebar/Routing** | Frontend | New admin pages | Add routes, nav items, lazy imports |
| **i18n** | Content | ~50 new keys | Update en.ts and es.ts |
| **DB performance** | Scale | audit_entries will be the highest-volume table | Need composite indexes: `(company_id, created_at)`, `(company_id, actor_id)`, `(company_id, resource_type, resource_id)` |
| **Request body capture** | Security | Sensitive fields in request body | Sanitization list must cover: password, token, magic_link, stripe_*, credit_card, secret |
| **Existing domain events** | No change | RequestEvent, AssetEvent, IncidentTimeline, RiskHistory remain independent | Document explicitly that E29 does NOT replace domain events |

---

## Slicing Assessment

**Size:** Large (8 user stories, 8 use cases, 4 entities, middleware, 4 Celery tasks, frontend, i18n)
**Slicing needed:** Yes — recommended 4 features

**Suggested slicing:**

| # | Feature | Complexity | Deps |
|---|---------|------------|------|
| F0 | Audit Foundation — entity, middleware, DB, hash chain | M | None |
| F1 | Audit UI & Export — list/detail pages, CSV/PDF export, compliance tagging | M | F0 |
| F2 | GDPR Operations — export, anonymization, request lifecycle | L | F0 |
| F3 | Retention & Integrity — retention policy, auto-purge, hash verification | S | F0 |

**Out of scope dependencies:**

| Item | Info Needed Now | Why |
|------|-----------------|-----|
| Compliance control catalog content | Yes | US-E29-004 ships a predefined catalog — need the actual list of NIS2/DORA/ISO controls |
| MCP middleware coverage | Yes | Must verify before F0 implementation |
| Sensitive field sanitization list | Yes | Need complete list of fields to redact from request_data |

---

## Time Constraints Assessment

**Deadline:** Not specified
**Type:** None
**Realistic:** Yes — no external pressure
**Calendar conflicts:** None
**Buffer included:** N/A

---

## Testing Assessment

**Tests defined:** Yes
**Critical scenarios identified:** Yes

| Test Type | Required | Defined | Gap |
|-----------|----------|---------|-----|
| Unit | Yes | Yes | Missing: hash chain edge cases (first entry, gap in chain, concurrent writes) |
| Integration | Yes | Yes | Missing: MCP tool call audit capture, plan gating 402 responses |
| E2E | No | No | N/A for this project |
| UAT | No | No | N/A |

**Test data requirements:** Not defined — need test fixtures for audit entries with hash chains

---

## Definition of Done Assessment

**DoD defined:** Yes (comprehensive)

| Criteria | Defined | Clear |
|----------|---------|-------|
| Acceptance criteria | Yes | Yes — 13 functional + 5 non-functional |
| Quality gates | Partial | Performance targets defined (< 5ms overhead, 100K export) but no load test methodology |
| Sign-off process | No | Not mentioned |
| Training needs | No | Not mentioned — admins will need guidance on compliance tagging |

---

## Red Flags

- [x] **Hash chain + compliance tag mutation contradiction** — AuditEntry is described as "immutable" but `compliance_tags` can be updated via PATCH. This breaks the hash chain since the entry data changes after hashing. **Must resolve**: either (a) exclude tags from hash computation, (b) use a separate join table for tags, or (c) create a new "tag_added" audit entry instead of mutating
- [x] **MCP SSE mounted app may bypass middleware** — FastAPI `app.mount()` creates a sub-application. `BaseHTTPMiddleware` on the parent app may not intercept requests to mounted sub-apps. Must verify or implement explicit audit capture in MCP layer
- [x] **Hash chain concurrency** — Multiple concurrent requests for the same company need the same `previous_hash`. If two requests write simultaneously, one will have a stale `previous_hash`. Need: (a) per-company lock/sequence, (b) accept eventual consistency with periodic chain repair, or (c) use a simpler integrity mechanism (per-entry hash without chaining)
- [x] **Middleware transaction coupling** — Requirement says "Insert AuditEntry in the same DB session (same transaction)". But middleware runs outside the route handler's DB session. The handler creates its own session via `Depends(get_db)`. Middleware would need a separate session or a hook into the handler's session. **Must resolve**: consider post-commit hook or separate transaction with best-effort guarantee
- [ ] ~~Missing rollback plan~~ — Not applicable (no deadline)

---

## Open Questions for Stakeholder

1. **Tag immutability**: Should compliance tags be stored in a separate table (preserving AuditEntry immutability) or inline on the entry (simpler but breaks immutability)?
2. **Hash chain concurrency**: Accept eventual consistency (periodic repair) or enforce strict ordering (per-company write lock)?
3. **Middleware vs. post-commit hook**: Given that middleware can't easily share the handler's DB transaction, should we use a post-commit hook pattern instead? Or accept audit entries in a separate transaction (risk: business op succeeds but audit write fails)?
4. **MCP coverage**: Verify that `BaseHTTPMiddleware` intercepts requests to `app.mount()`-ed sub-apps. If not, what's the capture strategy?
5. **GDPR request cancellation**: Should pending GDPR requests be cancellable?
6. **Super admin audit**: Should super admins have cross-company audit visibility? (Out of scope for E29?)
7. **Compliance catalog**: Who provides the predefined NIS2/DORA/ISO 27001 control list? Ship as seed data or configurable?

---

## Checklist Summary

### Business Alignment: 3/4 passed
- [x] Objective identified (Revenue & Churn)
- [x] KPIs defined (5 targets)
- [x] Evidence provided (regulatory citations)
- [ ] Revenue projection missing

### Content Completeness: 7/8 passed
- [x] Problem statement clear
- [x] Solution described
- [x] User stories with acceptance criteria
- [x] Entities defined with schemas
- [x] API endpoints listed
- [x] Non-goals documented
- [x] Architecture decisions documented
- [ ] Sensitive field sanitization list not specified

### Use Case Coverage: 6/8 passed
- [x] Happy paths covered (8 use cases)
- [x] Error scenarios documented
- [x] Alternative flows included
- [ ] Missing: remove tag, cancel GDPR, retry failed GDPR
- [ ] Missing: MCP tool call audit capture
- [x] GDPR anonymization edge cases (super_admin, self, already anonymized)
- [x] Retention purge side effects documented

### Entity States: 3/4 passed
- [x] AuditEntry immutability defined
- [x] GdprRequest state machine defined
- [ ] GdprRequest missing `cancelled` state and `started_at` field
- [x] Delete strategies defined per entity

### Collateral Impact: 10/12 passed
- [x] HTTP middleware impact identified
- [x] Auth dependency impact assessed
- [x] Celery task pattern identified
- [x] Feature gating strategy confirmed
- [x] User entity change identified
- [x] Notification events needed
- [x] Frontend impact identified
- [x] i18n impact quantified
- [ ] MCP SSE sub-app middleware coverage not verified
- [ ] DB indexing strategy for high-volume table not specified
- [x] Sensitive field sanitization mentioned
- [x] Domain events independence documented

### Slicing: 2/2 passed
- [x] Size assessed as Large
- [x] 4-feature slicing proposed

### Time Constraints: 2/2 passed
- [x] No deadline — no risk
- [x] Dependencies identified (E43, E6 — both done)

### Testing: 3/4 passed
- [x] Test types identified
- [x] Critical scenarios listed
- [ ] Hash chain concurrency/edge case tests not specified
- [x] Integration test scope defined

### Definition of Done: 3/4 passed
- [x] Acceptance criteria comprehensive
- [x] Non-functional requirements defined
- [ ] Load test methodology not specified
- [x] Infrastructure requirements listed

---

## Recommendations

1. **CRITICAL — Resolve hash chain + tag mutation conflict.** Recommended: store compliance tags in a separate `audit_entry_tags` join table, keeping AuditEntry truly immutable. Alternatively, exclude `compliance_tags` from the hash computation and document this.

2. **CRITICAL — Resolve middleware transaction coupling.** Recommended: use a separate transaction for audit writes with best-effort guarantee (if audit insert fails, log error but don't rollback business operation). This is simpler and more resilient than trying to share the handler's session.

3. **CRITICAL — Resolve hash chain concurrency.** Recommended for MVP: per-entry hash (hash of entry data only, no chaining to previous entry). This provides tamper detection per-entry without the concurrency complexity. Chain linking can be added later as an enhancement via a nightly batch job that links entries.

4. **HIGH — Verify MCP middleware coverage.** Test whether `BaseHTTPMiddleware` intercepts `app.mount()`-ed sub-apps. If not, add explicit audit capture in the MCP handler layer.

5. **MEDIUM — Add missing CRUD operations.** Add: remove tag endpoint, list tags endpoint, cancel GDPR request, retry GDPR request.

6. **MEDIUM — Add `started_at` to GdprRequest** and consider `cancelled` state.

7. **LOW — Define DB indexing strategy** for `audit_entries` table (high-volume). At minimum: `(company_id, created_at)`, `(company_id, actor_id, created_at)`, `(company_id, resource_type, resource_id)`.

8. **LOW — Define sensitive field sanitization list.** Document which request body fields are redacted: `password`, `password_hash`, `token`, `magic_link`, `secret`, `stripe_*`, `credentials`.
