# ADR-005: Page Authorization Boundaries & Cross-Page Access Prevention

## Status
Accepted

## Context
In a multi-page environment (e.g., an agency managing multiple corporate pages, or an e-commerce brand operating regional sub-pages), an AI agent might supply a `page_id` that belongs to an unauthorized account or an unrelated tenant. Relying simply on the possession of a Page ID is an insecure direct object reference (IDOR) vulnerability.

## Decision
All operations targeting a specific `page_id` must verify that the target `page_id` belongs to the authenticated user's authorized account list retrieved from Meta's `/me/accounts` endpoint.

## Rationale
1. **Zero-Trust Validation:** The server never trusts that an agent-supplied `page_id` is authorized without cross-checking against the token's granted pages.
2. **Fail Closed:** If a `page_id` is requested that is not present in the authorized accounts cache, the server fails closed with a `PageAuthorizationError`.
3. **Multi-Page Ready:** Supports future multi-page routing where the server selects the appropriate Page Access Token matching the target `page_id`.

## Consequences
- Requires an initial cached query to `/me/accounts` during startup or token renewal.
