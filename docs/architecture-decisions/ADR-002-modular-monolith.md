# ADR-002: Modular Monolith Architecture

## Status
Accepted

## Context
Enterprise software must balance testability, maintainability, and delivery speed. Over-engineering with microservices or external databases introduces premature operational burden, while a monolithic single-file script creates unmaintainable technical debt.

## Decision
We structure `fastmcp-facebook` as a **Modular Monolith** using Hexagonal Architecture (Ports and Adapters). The codebase is divided into four explicit layers:
1. `interfaces/mcp`: FastMCP tool registration and transport adapters.
2. `services`: Business operations (page discovery, post staging, comment triage).
3. `security`: Staging store, approval validation, secret redaction.
4. `infrastructure`: HTTPX client, retry policies, environment configuration.

## Rationale
1. **Decoupled Business Logic:** The underlying `MetaGraphClient` and application services can be imported and executed in other contexts (e.g., CLI, FastAPI, Celery) without any MCP dependencies.
2. **Deterministic Testability:** Every boundary can be mocked cleanly in `pytest` without spinning up external servers or databases.
3. **Evolutionary Simplicity:** A modular monolith can later be extracted into independent services if multi-tenant scaling demands it, without rewriting domain rules.

## Consequences
- Requires disciplined enforcement of package boundaries (no direct database or HTTP calls from interface handlers).
