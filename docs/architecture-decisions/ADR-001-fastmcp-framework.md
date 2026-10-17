# ADR-001: Adoption of FastMCP Framework

## Status
Accepted

## Context
Model Context Protocol (MCP) servers can be implemented either by writing low-level JSON-RPC protocol loops over standard input/output (`sys.stdin` / `sys.stdout`), or by utilizing a higher-level framework such as `mcp` / `fastmcp`. The initial prototype hand-rolled its own JSON-RPC protocol loop in `server.py`.

## Decision
We adopt **FastMCP 2.0+** (`mcp` Python SDK) as the official protocol framework for `facebook-pages-mcp`.

## Rationale
1. **Automated Schema Generation:** FastMCP inspects Python type hints and Pydantic v2 models to automatically generate valid OpenAPI/JSON Schema specifications for MCP clients.
2. **Transport Agnosticism:** FastMCP abstracts transport mechanics, allowing `facebook-pages-mcp` to support both local standard I/O (`stdio`) and remote Streamable HTTP / Server-Sent Events (SSE) with minimal code changes.
3. **Standard Error Mapping:** Provides standardized JSON-RPC error codes and exception wrappers out of the box.

## Consequences
- Requires `mcp>=1.0.0` and `pydantic>=2.7.0` as core dependencies.
- Eliminates brittle hand-rolled JSON parsing logic from our codebase.
