# Tasks: F6 — SSE Transport

## Implementation Tasks

### 1. Configuration
- [x] Add `MCP_SSE_PATH` to `MCPSettings` in `core/config.py`

### 2. Authentication
- [x] Add `authenticate_bearer_token()` to `adapters/mcp/auth.py` (API key + JWT)

### 3. SSE Transport App
- [x] Create `adapters/mcp/sse.py` with Starlette app
- [x] `GET /sse` — SSE connection with auth from Authorization header
- [x] `POST /messages` — Message forwarding to SSE transport

### 4. FastAPI Integration
- [x] Edit `app.py` — conditional mount when `MCP_ENABLED=true`

### 5. Configuration Documentation
- [x] Update `.env.example` with MCP variables

### 6. Unit Tests
- [x] `tests/unit/mcp/test_sse.py` (8 tests)

### 7. Verification
- [x] Lint passes
- [x] New tests pass (8/8)
- [x] Full unit suite passes (`make test` — 596 passed)

### 8. Progress Tracking
- [x] Mark all tasks done
- [x] Update `slicing.md` — F6 status to Done
