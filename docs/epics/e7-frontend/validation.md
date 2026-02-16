# E7: Frontend - Validation

**Date:** 2026-02-16

---

## Codebase Alignment

- All 61 backend endpoints implemented and tested (414 tests pass)
- Response format consistent: `{ data }` or `{ data, meta }` envelope
- Auth: Magic link + JWT (24h expiry on magic link, JWT in Authorization header)
- WebSocket: `WS /ws?token=<jwt>` with JSON event push
- CORS configured for `FRONTEND_URL` (default `http://localhost:5173` — Vite default)

## Dependencies

- Node.js / npm (standard tooling, no special server deps)
- Backend running on `http://localhost:8000`
- No new backend changes needed

## Scope

- Pure frontend — no backend modifications
- All pages are read/write against existing API
- WebSocket for real-time notifications only (no SSR, no server components)

## Risks

- **Chart library size**: Recharts is lightweight enough for the 4 dashboard charts needed
- **PDF download**: Signed URL redirect — no blob handling needed, just `window.open(url)`
- **CSV import**: File upload via FormData, max 1MB
- **WebSocket reconnection**: Need exponential backoff logic
