# Tasks: F3 — AI Article Suggestions

**Feature:** [requirements.md](../../requirements.md)
**Design:** [../../design.md](../../design.md)
**Date:** 2026-02-23

## Summary

| # | Task | Complexity | Phase |
|---|------|-----------|-------|
| 1 | Suggest repository method | S | Infra |
| 2 | GET /suggest endpoint | S | HTTP |

## Detailed Tasks

### Task 1: Suggest repository method
- **File:** `src/kb_bc/article/infrastructure/repository.py`
- **What:** suggest() with word-level matching (splits text into words >2 chars, matches any word in title/content)
- **Note:** Built during F0 implementation
- [x] Done

### Task 2: Suggest endpoint
- **File:** `adapters/http/api/kb/routers.py`
- **What:** GET /suggest (employee+) with text and limit params, returns matching published articles
- **Note:** Built during F0 implementation
- [x] Done
