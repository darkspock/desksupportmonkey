# Slicing: E46 - White Label & Multi-Brand Deployment

**Epic:** [requirements.md](requirements.md)
**Date:** 2026-02-24
**Total Features:** 4

## Slicing Rationale

The epic is sliced into four vertical features that build on each other:

1. **F0** establishes the brand config layer and removes hardcoded references — after this, the app is "brand-aware" but still looks the same with defaults
2. **F1** adds asset organization and color theming — after this, a second brand can have its own logo and colors
3. **F2** brands the backend outputs (emails and PDFs) — after this, the entire user experience is white-labeled end-to-end
4. **F3** adds the build/deploy tooling — after this, producing and deploying a branded build is a single command

Each feature delivers incrementally: F0 alone is useful (config-driven branding), F0+F1 enables visual customization, F0+F1+F2 covers all touchpoints, and F0+F1+F2+F3 completes the full white-label pipeline.

## Dependency Graph

```
F0: Brand Configuration Layer (frontend)
    │
    ├── F1: Brand Assets & Theming (frontend)
    │
    ├── F2: Backend Branding — Emails & PDFs (backend)
    │
    └── F3: Build & Deploy Tooling (depends on F0 + F1 + F2)
```

## Features Summary

| # | Feature | Dependencies | Value Delivered | Complexity | Status |
|---|---------|--------------|-----------------|------------|--------|
| 0 | Brand Configuration Layer | None | All frontend branding driven by config, zero hardcoded refs | M | Done |
| 1 | Brand Assets & Theming | F0 | Per-brand logos, favicons, and color palettes | S | Done |
| 2 | Backend Branding — Emails & PDFs | F0 | Email templates and PDF reports show configured brand | S | Done |
| 3 | Build & Deploy Tooling | F0, F1, F2 | One-command branded builds with DB isolation | S | Done |

## Recommended Order

1. **Feature 0** — Foundation: create brand config, replace all hardcoded references
2. **Feature 1** — Visual identity: organize brand assets, add color theme overrides
3. **Feature 2** — Backend outputs: brand-aware emails and PDF reports
4. **Feature 3** — Automation: build scripts, env files, deploy targets

## Slicing Validation

- [x] No circular dependencies
- [x] Unidirectional dependency flow
- [x] Each feature independently deployable
- [x] Vertical slices (not horizontal layers)
- [x] Shared foundation identified (F0)
- [x] No overlapping scope
- [x] Each feature delivers minimum viable value
- [x] All epic scope covered

## Risk Notes

- Vite's `index.html` title cannot use `import.meta.env` directly — will need `vite-plugin-html` or a post-build replacement strategy
- Brand-specific CSS may need a Vite plugin or dynamic import depending on approach chosen
- Email and PDF templates may have brand references in unexpected places — need thorough grep before marking complete
