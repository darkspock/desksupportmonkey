# Requirement Validation Report

**Document:** E46 - White Label & Multi-Brand Deployment
**Date:** 2026-02-24
**Type:** Epic (Full Validation)
**Status:** Valid (minor gaps)

## Summary

Well-structured epic with clear problem statement, 6 user stories with testable acceptance criteria, explicit technical constraints, and well-defined scope boundaries. This is a **frontend-only configuration epic** — no new domain entities, no state machines, no API changes. The main gaps are: missing business alignment/KPIs (acceptable for an internal tooling epic), no formal testing section, and a few edge cases worth considering.

## Business Alignment Assessment

**Primary Objective:** Operational / Sales enablement (deploy same product under multiple brands)
**Contribution:** Unclear — no revenue/customer data provided
**KPIs Defined:** No
**Justification Type:** Missing

### Justification Quality

| Criteria | Status | Issue |
|----------|--------|-------|
| Specific numbers | No | No data on how many brands/deployments planned |
| Evidence sources | No | No customer requests or contracts cited |
| Revenue impact | No | No revenue projection per additional brand |
| Customer names/tickets | No | No specific demand evidence |

### Experimentation Assessment

**Is this an experiment?** No

**RED FLAGS:**
- [x] Missing revenue/cost impact (not an experiment)
- [x] No evidence provided (not an experiment)

> **Note:** This is acceptable for an internal infrastructure/tooling epic. The need is self-evident from the stated requirement of deploying two instances with different branding. Proceed anyway? The user has already confirmed the need.

## Entities Identified

| Entity | CRUD Coverage | States Defined | Delete Strategy |
|--------|---------------|----------------|-----------------|
| Brand Config | N/A (static config object) | N/A | N/A |
| Brand Assets | Create folder + files | N/A | N/A |
| Brand Env File | Create + document | N/A | N/A |

> **No domain entities are created or modified.** This epic is purely frontend configuration and build tooling. CRUD, state machines, and delete strategies do not apply.

## Missing Use Cases

| Use Case | Reason | Priority | Question for Stakeholder |
|----------|--------|----------|--------------------------|
| Brand validation at build time | What happens if `VITE_BRAND_SLUG` points to a non-existent `brands/` folder? Build should fail with clear error | Low | Should Vite config validate brand folder existence? |
| Brand config in backend emails | Email templates (magic link, notifications) may contain the app name. These are not covered | Medium | Do email templates need brand-aware subject lines or body text? |
| Brand in PDF reports | Report headers/footers may show "DeskSupportMonkey". Jinja2 templates not addressed | Medium | Should PDF report branding also be configurable per deployment? |
| Brand in MCP server | MCP server metadata (`server_name`, tool descriptions) contains "DSM" references | Low | Should MCP server name also be brand-configurable? |
| Brand in API responses | Health check or error responses may contain app name | Low | Any API response that exposes the brand name? |

## Missing State Information

| Entity | Missing Info | Question |
|--------|--------------|----------|
| N/A | No stateful entities in this epic | — |

## Collateral Impact

| Component | Type | Impact | Action Required |
|-----------|------|--------|-----------------|
| `web/app/public/logo.png` | Asset removal | Old logo path breaks if removed before all refs updated | Ensure F0 completes before F1 removes old assets |
| `locales/en.ts`, `es.ts` | String removal | Removing brand keys from i18n could break components still referencing them | Update components (F0) before removing i18n keys |
| `.gitignore` | Config | Brand-specific `.env.dsm`, `.env.formal` files should be gitignored (contain secrets) | Add `.env.*` pattern to .gitignore |
| `web/app/src/lib/i18n.tsx` | LocalStorage key | Uses `'dsm.language'` — should this be brand-aware? | Low priority, but `{slug}.language` avoids conflicts if two brands run on same domain |
| `Makefile` | Existing targets | New `build-brand` / `start-brand` targets must not conflict with existing `build` / `start` | Use distinct target names (already planned) |
| Backend email templates | Templates | Magic link emails may reference "DeskSupportMonkey" in subject/body | Not covered — consider as follow-up |
| PDF report templates | Templates | Jinja2 templates in `templates/` may have hardcoded brand name | Not covered — consider as follow-up |

## Slicing Assessment

**Size:** Medium
**Slicing needed:** Yes (already sliced into 3 features)
**Slicing quality:** Good — vertical slices with clear dependency chain (F0 → F1 → F2)

**Out of scope dependencies:**

| Item | Info Needed Now | Why |
|------|-----------------|-----|
| Backend email branding | No | Can be a separate follow-up feature |
| PDF report branding | No | Can be a separate follow-up feature |
| MCP server branding | No | Low impact, can be done later |

## Time Constraints Assessment

**Deadline:** Not specified
**Type:** None
**Reason:** N/A
**Realistic:** Yes — scope is small (M complexity, ~13 tasks)
**Calendar conflicts:** None identified
**Buffer included:** N/A

### Deadline Risk Analysis

| Risk | If deadline missed | Mitigation |
|------|-------------------|------------|
| N/A | No deadline set | — |

## Testing Assessment

**Tests defined:** No
**Critical scenarios identified:** Partially (grep validation in Task 7)

| Test Type | Required | Defined | Gap |
|-----------|----------|---------|-----|
| Unit | No | No | No domain logic to unit test |
| Integration | Yes | No | Should verify build produces correct brand values in output HTML/JS |
| E2E | Yes | No | Should verify branded build renders correct logo, name, and colors |
| UAT | No | No | Visual verification by deployer |

**Test data requirements:** Brand asset files (logo, favicon) for at least 2 brands

> **Gap:** No testing user story or acceptance criteria. Consider adding: "Build for brand X and verify output HTML title, favicon path, and brand name in JS bundle match config."

## Definition of Done Assessment

**DoD defined:** Partially

| Criteria | Defined | Clear |
|----------|---------|-------|
| Acceptance criteria | Yes | Yes — each US has checkboxes |
| Quality gates | Partially | Task 7 grep validation, but no build verification |
| Sign-off process | No | Who verifies the branded build looks correct? |
| Training needs | No | Guide in F2-Task 3 covers this |

## Red Flags

- [ ] No business alignment / KPIs (acceptable for tooling epic)
- [ ] Backend branding not covered (emails, PDFs, MCP) — could surprise deployers who expect full white-label
- [ ] No testing criteria beyond grep validation
- [x] `.env.*` files with DATABASE_URL could be accidentally committed (need gitignore)

## Open Questions for Stakeholder

1. **Email templates:** Should magic link and notification emails also show the configured brand name instead of "DeskSupportMonkey"?
2. **PDF reports:** Should report headers/footers be brand-aware?
3. **i18n localStorage key:** Currently `dsm.language` — should it be `{slug}.language` to avoid conflicts if two brands are served from the same domain?
4. **Brand asset validation:** Should the build fail with a clear error if the brand folder doesn't exist, or silently fall back to defaults?
5. **How many brands** are planned initially? Just 2 (informal + formal), or more?

## Checklist Summary

### Business Alignment: 0/4 passed
(Acceptable — internal tooling epic, need is self-evident)

### Content Completeness: 6/6 passed
- [x] Problem statement clear
- [x] Goals defined
- [x] User stories with acceptance criteria
- [x] Technical constraints documented
- [x] Out of scope defined
- [x] Dependencies listed

### Use Case Coverage: 3/5 passed
- [x] Core use case (build-time brand config)
- [x] Asset organization
- [x] Build tooling
- [ ] Backend branding (emails, PDFs) — not covered
- [ ] Build validation on invalid brand slug — not covered

### Entity States: N/A
(No stateful entities)

### Collateral Impact: 4/7 identified
- [x] File path changes (logo.png)
- [x] i18n string removal
- [x] Makefile additions
- [x] gitignore for env files
- [ ] Email templates
- [ ] PDF templates
- [ ] LocalStorage key conflict

### Slicing: 5/5 passed
- [x] Vertical slices
- [x] Clear dependencies
- [x] Each feature delivers value
- [x] No overlapping scope
- [x] Full epic coverage

### Time Constraints: N/A
(No deadline)

### Testing: 1/4 passed
- [x] Grep validation defined (Task 7)
- [ ] Build output verification
- [ ] Visual rendering verification
- [ ] Multi-brand build comparison

### Definition of Done: 2/4 passed
- [x] Acceptance criteria testable
- [x] Training/docs planned (F2-Task 3)
- [ ] Quality gates incomplete
- [ ] Sign-off process undefined

## Recommendations

1. **Add a note in Out of Scope** clarifying that backend branding (emails, PDFs, MCP server name) is intentionally deferred — so deployers know what to expect
2. **Add `.env.*` to `.gitignore`** as part of F2 to prevent accidental secret commits
3. **Consider adding a build-time validation** in `vite.config.ts` that checks `brands/{slug}/` folder exists and contains required files (logo.png at minimum)
4. **Add a simple smoke test**: after `make build-brand BRAND=dsm`, verify the output `index.html` contains the expected title and favicon path
5. **LocalStorage key**: minor, but change `dsm.language` to `${brand.slug}.language` in F0 to future-proof

**Overall verdict:** Epic is well-defined and ready for implementation. The gaps are minor and can be addressed as follow-ups. Proceed.
