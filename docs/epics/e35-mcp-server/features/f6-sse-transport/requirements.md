# Feature: SSE Transport

**Parent Epic:** [E35 - MCP Server](../../requirements.md)
**Feature #:** F6
**Dependencies:** F1 (MCP Server Core)
**Complexity:** M

---

## Scope

### Included

Add Server-Sent Events (SSE) transport to the MCP server, enabling production HTTP-based access for AI assistants that connect over the network rather than via subprocess stdio.

**SSE endpoint:**
- Mount the MCP SSE transport in the existing FastAPI application at a configurable path (default: `/mcp/sse`)
- Conditional mounting based on `MCP_ENABLED` environment variable
- Configurable SSE path via `MCP_SSE_PATH` environment variable

**FastAPI integration:**
- Modify `app.py` to conditionally mount the MCP SSE endpoint when `MCP_ENABLED=true`
- Integration with existing CORS middleware (MCP clients may connect cross-origin)
- Integration with existing security middleware and error handling
- The SSE endpoint must coexist with all existing HTTP API routes without interference

**Authentication:**
- API key authentication via HTTP headers (e.g., `Authorization: Bearer dsm_...`) on the SSE connection
- JWT authentication passthrough for clients that already have tokens
- Same auth flow as stdio transport (resolve key/token to user context with company_id, role)

**Configuration:**
- `MCP_ENABLED` -- boolean, enables/disables the MCP server entirely (default: false)
- `MCP_SSE_PATH` -- string, the URL path for the SSE endpoint (default: `/mcp/sse`)
- Update `.env.example` with all MCP-related environment variables

### Excluded

- stdio transport (already implemented in F1)
- Individual tool definitions (F2-F5)
- API key management entity/endpoints (F0)
- WebSocket transport (not part of MCP standard)
- Any modifications to existing domain, application, or infrastructure layers

---

## User Value

SSE transport makes the MCP server accessible to AI assistants running on remote machines or in cloud environments. While stdio requires the MCP server to run as a local subprocess (suitable for development), SSE enables:
- **Claude Desktop** and **Cursor** to connect to a centrally hosted DeskSupportMonkey instance over HTTP.
- **Custom AI agents** to interact with the MCP server from any network location.
- **Production deployments** where the MCP server runs alongside the existing API server without requiring additional processes.

This is the production-grade transport that makes the MCP server usable beyond local development.

---

## Acceptance Criteria

### SSE Endpoint
- [ ] MCP server is accessible via SSE at the configured path (default `/mcp/sse`)
- [ ] SSE endpoint is only mounted when `MCP_ENABLED=true`
- [ ] SSE path is configurable via `MCP_SSE_PATH` environment variable
- [ ] SSE endpoint follows the MCP SSE transport specification (bidirectional via SSE events + POST messages)
- [ ] Multiple concurrent SSE connections are supported

### Authentication
- [ ] API key authentication works via SSE (key passed in HTTP headers on initial connection)
- [ ] JWT authentication works via SSE (token passed in HTTP headers)
- [ ] Unauthenticated SSE connections are rejected with appropriate error
- [ ] Invalid/revoked API keys are rejected
- [ ] Authenticated user context (company_id, role) is propagated to all tool calls within the session

### Integration with Existing App
- [ ] Existing HTTP API endpoints are unaffected (all routes continue to work)
- [ ] CORS middleware applies to SSE endpoint (configurable origins)
- [ ] The application starts normally when `MCP_ENABLED=false` (SSE endpoint not mounted)
- [ ] The application starts normally when `MCP_ENABLED=true` (SSE endpoint mounted alongside HTTP routes)
- [ ] `make start` works with MCP enabled and disabled

### Tool Accessibility
- [ ] All registered MCP tools are callable via SSE transport (same behavior as stdio)
- [ ] Role-based tool filtering works identically over SSE and stdio
- [ ] Multi-tenant isolation is maintained over SSE connections

### Configuration
- [ ] `.env.example` updated with `MCP_ENABLED`, `MCP_SSE_PATH` variables with documentation comments
- [ ] Default values are sensible: `MCP_ENABLED=false`, `MCP_SSE_PATH=/mcp/sse`

### Testing
- [ ] `make test` passes (unit tests)
- [ ] Integration tests verify SSE endpoint responds and accepts connections
- [ ] Integration tests verify authentication over SSE
- [ ] Tested with at least one real MCP client (Claude Desktop or Cursor) to confirm compatibility

---

## Technical Scope

### Entities (owned)

None. This feature creates no new entities.

### Entities (used)

- `ApiKey` (mcp_bc) -- for API key authentication resolution
- `User` (auth_bc) -- for user context after authentication

### Key Components

| Component | Action | Description |
|-----------|--------|-------------|
| `app.py` | Modify | Add conditional MCP SSE mount when `MCP_ENABLED=true` |
| `adapters/mcp/server.py` | Modify | Add SSE transport setup alongside existing stdio transport |
| `adapters/mcp/auth.py` | Modify | Support auth via HTTP headers (SSE) in addition to existing auth flow |
| `core/config.py` or equivalent | Modify | Add `MCP_ENABLED`, `MCP_SSE_PATH` configuration variables |
| `.env.example` | Modify | Add MCP configuration variables with documentation |
| `tests/integration/test_mcp_sse.py` | Create | Integration tests for SSE transport, auth, and tool calls |

---

## Notes

- The MCP SSE transport specification uses a combination of Server-Sent Events (server-to-client) and HTTP POST (client-to-server). The `mcp` Python SDK provides built-in support for this transport mode -- the implementation should use the SDK's SSE server adapter rather than implementing the protocol manually.
- Middleware ordering matters: the SSE endpoint needs CORS headers but should not go through the same JSON body parsing middleware as REST endpoints. FastAPI's sub-application mounting pattern may be appropriate.
- The SSE endpoint should be tested with a real MCP client to catch protocol-level issues that unit tests cannot detect. Claude Desktop and Cursor both support SSE transport and can be used for manual verification.
- When `MCP_ENABLED=false`, the SSE route should not even be registered in FastAPI, not just return 404. This avoids exposing any MCP-related paths in production if MCP is not desired.
- Consider adding a health check or info endpoint (e.g., `/mcp/info`) that returns the MCP server name and version, useful for client configuration.
