# Epic Slicing: E35 MCP Server

**Epic:** [requirements.md](requirements.md)
**Date:** 2026-02-17
**Total Features:** 8

## Slicing Rationale

The MCP server epic has a clear foundational layer (API keys + MCP server core) that all tools depend on, followed by tool groups that can be implemented independently in parallel. The tools are grouped by bounded context to avoid overlapping scope — each tool module maps to a single adapter file. The frontend page is isolated as the final feature since it depends on the API key endpoints but not on the MCP tools themselves.

## Dependency Graph

```
F0: API Key Management (BC + migration + HTTP endpoints)
    │
    ├── F1: MCP Server Core (server setup, auth, stdio transport, role filtering)
    │       │
    │       ├── F2: Asset & Request Tools (20 tools - highest value)
    │       │
    │       ├── F3: User, Department & Company Tools (17 tools)
    │       │
    │       ├── F4: Dashboard, Report & My Tools (18 tools)
    │       │
    │       ├── F5: Auth & API Key MCP Tools (5 tools)
    │       │
    │       └── F6: SSE Transport (production transport, mount in FastAPI)
    │
    └── F7: API Keys Frontend Page (admin UI for key management)
```

## Features Summary

| # | Feature | Dependencies | Value Delivered | Status |
|---|---------|--------------|-----------------|--------|
| F0 | API Key Management | None | Users can create/revoke API keys for MCP auth | Done |
| F1 | MCP Server Core | F0 | MCP server boots, authenticates, filters tools by role (stdio) | Done |
| F2 | Asset & Request Tools | F1 | AI can manage assets and service requests (20 tools) | Done |
| F3 | User, Dept & Company Tools | F1 | AI can manage users, departments, companies (17 tools) | Done |
| F4 | Dashboard, Report & My Tools | F1 | AI can query dashboard, generate reports, access personal data (18 tools) | Done |
| F5 | Auth & API Key MCP Tools | F1 | AI can manage its own auth and API keys (5 tools) | Done |
| F6 | SSE Transport | F1 | MCP server accessible via HTTP/SSE for production use | Done |
| F7 | API Keys Frontend Page | F0 | Admins can create/manage API keys from the web UI | Done |

## Recommended Implementation Order

1. **F0: API Key Management** — Must be first. Creates the `api_keys` table, entity, repo, and HTTP endpoints. Everything else depends on this.
2. **F1: MCP Server Core** — Second. Sets up the MCP server, auth middleware, tool registry, role filtering, and stdio transport. After this, the server boots and authenticates but has no tools yet.
3. **F2: Asset & Request Tools** — Third. Highest-value tools — AI can manage the core business objects (assets + requests = 20 tools). This alone makes the MCP server useful.
4. **F3: User, Dept & Company Tools** — Can run in parallel with F2. Admin/super-admin management operations.
5. **F4: Dashboard, Report & My Tools** — Can run in parallel with F2/F3. Read-heavy tools for analytics and personal data.
6. **F5: Auth & API Key MCP Tools** — Small feature, can run in parallel with F2-F4. Lets AI manage its own keys.
7. **F6: SSE Transport** — After core tools work via stdio. Adds HTTP-based transport for production deployments.
8. **F7: API Keys Frontend Page** — Can be done anytime after F0. Independent of MCP tools.

**Parallelization:** F2, F3, F4, F5 can all be implemented in parallel after F1 is complete. F7 can be done in parallel with any feature after F0.

## Slicing Validation

- [x] No circular dependencies
- [x] Unidirectional dependency flow (F0 → F1 → F2-F6, F0 → F7)
- [x] Each feature independently deployable
- [x] Vertical slices — each feature delivers complete tools end-to-end
- [x] Shared foundation identified (F0 + F1)
- [x] No overlapping scope — each tool group maps to separate files
- [x] Each feature delivers minimum viable value
- [x] All epic scope covered (60 tools + frontend + 2 transports)

## Risk Notes

- **MCP SDK stability:** The `mcp` Python package is relatively new. Pin the exact version in `pyproject.toml` and test with the specific Claude Desktop/Cursor versions available at implementation time.
- **Tool parameter types:** MCP tool parameters are JSON Schema. Some DSM parameters (dates, enums) need careful type mapping to ensure AI assistants provide valid values.
- **SSE in FastAPI:** Mounting an MCP SSE endpoint alongside the existing FastAPI app may require careful middleware ordering. F6 is deliberately separate so this can be tested independently.
