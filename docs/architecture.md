# System Architecture: facebook-pages-mcp

## 1. Architectural Vision & Boundaries

`facebook-pages-mcp` is designed as a **Modular Monolith** adhering to Hexagonal Architecture (Ports and Adapters) principles. The goal is to provide a zero-leakage, security-first bridge between AI assistants communicating over the Model Context Protocol (MCP) and Meta's official Graph API.

### Logical Boundaries

```mermaid
graph TD
    subgraph "External World (Untrusted)"
        Client["MCP Client / AI Agent"]
        MetaAPI["Meta Graph API (https://graph.facebook.com)"]
    end

    subgraph "facebook-pages-mcp Core"
        subgraph "Inbound Ports (Interfaces)"
            FastMCPServer["FastMCP Transport & Tool Registry"]
            CLIRunner["Optional CLI / Health Runner"]
        end

        subgraph "Application Core (Domain Services)"
            PageService["Page Management Service"]
            PostService["Post Lifecycle Service"]
            CommentService["Comment Moderation Service"]
            StagedActionStore["Two-Stage Approval Store"]
        end

        subgraph "Security & Policy"
            AuthorizationGate["Page Authorization Gate"]
            SecretScrubber["Log/Error Secret Sanitizer"]
            AuditRecorder["Structured Audit Logger"]
        end

        subgraph "Outbound Adapters (Infrastructure)"
            HTTPXClient["Resilient Graph Client (HTTPX)"]
            RateLimiter["Adaptive Backoff Rate Limiter"]
            ConfigProvider["Environment & Settings Provider"]
        end
    end

    Client -->|"JSON-RPC / stdio"| FastMCPServer
    FastMCPServer --> AuthorizationGate
    AuthorizationGate --> PageService
    AuthorizationGate --> PostService
    AuthorizationGate --> CommentService

    PostService --> StagedActionStore
    CommentService --> StagedActionStore
    StagedActionStore --> AuditRecorder

    PageService --> HTTPXClient
    PostService --> HTTPXClient
    CommentService --> HTTPXClient

    HTTPXClient --> RateLimiter
    HTTPXClient --> SecretScrubber
    HTTPXClient --> ConfigProvider
    HTTPXClient -->|"HTTPS / TLS 1.3"| MetaAPI
```

---

## 2. Layer Definitions & Separation of Concerns

### Layer 1: MCP Interface Layer (`fastmcp_facebook/interfaces/mcp/`)
- **Responsibilities:** Registers tools using the FastMCP framework, manages JSON-RPC serialization, and transforms domain objects into token-optimized response dictionaries.
- **Rules:** Contains no direct HTTP calls or business logic. All validation is driven by strict Pydantic v2 schemas.

### Layer 2: Application Service Layer (`fastmcp_facebook/services/`)
- **Responsibilities:** Implements use cases (discovering pages, staging posts, verifying approval tokens, publishing approved actions).
- **Rules:** Agnostic of MCP transport. Can be invoked directly from CLI, test harnesses, or background jobs.

### Layer 3: Security & Governance Layer (`fastmcp_facebook/security/`)
- **Responsibilities:**
  - Enforces two-stage approval lifetimes and single-use constraints.
  - Sanitizes all outgoing log events and error payloads to eliminate credential leakage.
  - Generates tamper-evident audit logs (`stderr`) for every write preparation and execution.

### Layer 4: Infrastructure & Meta Integration Layer (`fastmcp_facebook/infrastructure/`)
- **Responsibilities:**
  - Manages HTTP/2 and HTTP/1.1 connection pools using `httpx.AsyncClient`.
  - Parses Meta Graph API rate-limit headers (`X-App-Usage`, `X-Page-Usage`).
  - Implements bounded exponential backoff for transient network errors ($500$, $502$, $503$, $504$).

---

## 3. Data Flow: Two-Stage Publishing Flow

```mermaid
sequenceDiagram
    autonumber
    actor Reviewer as Human Reviewer
    participant Agent as AI Assistant
    participant FastMCP as MCP Interface Layer
    participant Service as PostService
    participant Store as StagedActionStore
    participant Meta as Meta Graph API

    Agent->>FastMCP: posts_prepare(page_id, message, link)
    FastMCP->>Service: prepare_post(request)
    Service->>Service: Validate constraints (character limits, URLs)
    Service->>Store: store_action(action_type, payload, ttl=900s)
    Store-->>Service: staged_action_id, action_hash
    Service-->>FastMCP: StagedActionPreview
    FastMCP-->>Agent: Returns preview & action_id
    Agent-->>Reviewer: "I prepared this post. ID: act_9876. Please approve."
    Reviewer->>Agent: "Approved. Proceed."
    Agent->>FastMCP: posts_publish_approved(staged_action_id, approval_token)
    FastMCP->>Service: publish_approved(staged_action_id, token)
    Service->>Store: claim_action(staged_action_id)
    alt Action Expired or Already Used
        Store-->>Service: Error: Token invalid or expired
        Service-->>FastMCP: StagingSecurityError
        FastMCP-->>Agent: Failure: Request blocked
    else Action Valid
        Store->>Store: Mark action consumed
        Service->>Meta: POST /{page-id}/feed (HTTPX)
        Meta-->>Service: 200 OK {id: "post_12345"}
        Service-->>FastMCP: PublishedResult
        FastMCP-->>Agent: Success {post_id, url}
        Agent-->>Reviewer: "Post successfully published to Facebook Page!"
    end
```

---

## 4. Evolution Toward Remote Deployment

While initial releases target local `stdio` execution for desktop AI tools (Claude Desktop, Cursor), the architecture is designed to evolve cleanly toward remote Streamable HTTP / Server-Sent Events (SSE):

1. **Identity & Multi-Tenancy:**
   - In local `stdio` mode, authorization is bound to the local OS user process and local environment variables.
   - In remote mode, the MCP server will integrate OAuth 2.1 Bearer Token validation, mapping authenticated tenant IDs to isolated per-tenant Page tokens stored in a secure secrets manager.
2. **Stateless Staging Store:**
   - The in-memory `StagedActionStore` will be backed by Redis or an encrypted transactional database with atomic token consumption (`GETDEL` / `UPDATE ... WHERE consumed=false`).
