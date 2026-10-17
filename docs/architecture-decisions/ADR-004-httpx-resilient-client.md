# ADR-004: HTTPX Resilient Graph API Client

## Status
Accepted

## Context
The initial prototype used Python's standard `urllib.request` library. While dependency-free, `urllib.request` lacks async/await capabilities, persistent HTTP connection pooling, clean request/response event hooks, and modern timeout configurations.

## Decision
We adopt **HTTPX** (`httpx.AsyncClient`) as the primary HTTP engine for interacting with the Meta Graph API.

## Rationale
1. **Connection Pooling & Performance:** Reuses persistent TLS 1.3 TCP connections, eliminating repeated SSL handshake overhead for sequential API calls.
2. **Event Hook Interceptors:** Allows registering event hooks to automatically sanitize secrets from outgoing logs and decode Meta rate-limit headers (`X-App-Usage`, `X-Page-Usage`).
3. **Async & Sync Support:** Supports standard Python `asyncio` workflows.
4. **Mockability:** Highly compatible with `pytest-mock` and `respx` for deterministic offline integration testing.

## Consequences
- Adds `httpx>=0.27.0` as an external dependency.
