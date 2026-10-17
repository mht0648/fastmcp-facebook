# Deployment & Operations Guide: facebook-pages-mcp

This document covers operational requirements, local deployment, environment configuration, and future remote hosting.

---

## 1. Local stdio Deployment (Primary Target)

In local stdio mode, the MCP server is launched by the client (Claude Desktop, Cursor, Antigravity) as a subprocess. Communication occurs over standard input (`stdin`) and standard output (`stdout`).

### Operational Guidelines:
1. **Never print to `stdout`:** The JSON-RPC transport protocol strictly reserves `stdout` for valid JSON-RPC 2.0 messages. Any unexpected text (e.g. `print("connecting...")`) will corrupt the client's parser and crash the MCP connection.
2. **Log exclusively to `stderr`:** All operational logging, diagnostics, and audit events must be directed to `sys.stderr`.
3. **Subprocess Lifetime:** The server starts when the AI assistant initiates a session and terminates when the client closes.

---

## 2. Environment Variables Specification

| Variable | Type | Required | Default | Description |
| :--- | :---: | :---: | :---: | :--- |
| `FB_PAGE_ID` | String | Yes | None | The target Facebook Page ID to manage. |
| `FB_PAGE_ACCESS_TOKEN` | String | Yes | None | Long-lived or Permanent Page Access Token. |
| `FB_API_VERSION` | String | No | `v21.0` | Meta Graph API version string. |
| `ENABLE_PAGE_PUBLISHING` | Boolean | No | `false` | Master kill-switch. When `false`, all live write operations are rejected. |
| `STAGING_TTL_SECONDS` | Integer | No | `900` | Expiration time for staged post action IDs (default: 15 minutes). |
| `LOG_LEVEL` | String | No | `INFO` | Logging verbosity (`DEBUG`, `INFO`, `WARNING`, `ERROR`). |

---

## 3. Remote Deployment Evolution (Streamable HTTP / SSE)

When deploying `facebook-pages-mcp` as a remote cloud service (e.g., Docker, Kubernetes, AWS ECS):

1. **Transport Migration:** FastMCP natively supports Server-Sent Events (SSE) and HTTP POST endpoints.
2. **Reverse Proxy / TLS Termination:**
   - Must sit behind an API gateway (e.g., Nginx, Envoy, Cloudflare) enforcing TLS 1.3.
   - Enforce rate-limiting at the ingress level.
3. **Secret Storage:**
   - Transition from `.env` to AWS Secrets Manager, HashiCorp Vault, or Google Secret Manager.
4. **Approval State Persistence:**
   - Replace in-memory `StagedActionStore` with Redis or PostgreSQL to preserve pending approvals across server restarts or scaled replicas.
