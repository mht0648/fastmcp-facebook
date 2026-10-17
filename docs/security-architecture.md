# Security Architecture: fastmcp-facebook

## 1. Principles of Operation

The security architecture of `fastmcp-facebook` is governed by five non-negotiable principles:

1. **Zero Trust across Boundaries:** We treat all inputs from AI agents, MCP clients, and Meta Graph API responses as untrusted.
2. **Fail Securely (Fail-Closed):** If token validity, page ownership, or action approvals cannot be proven unambiguously, operations immediately terminate with an error.
3. **Least Privilege:** Tools only request and return fields explicitly necessary for the requested operation (`?fields=id,name,link` instead of default wildcard objects).
4. **Defense in Depth:** We do not rely solely on system prompts to keep AI agents safe; server-side cryptographic checks enforce authorization.
5. **Zero Secret Leakage:** Access tokens, client secrets, and internal approval nonces must never be transmitted to the LLM agent or output logs.

---

## 2. Authentication & Authorization Architecture

### A. Meta Graph API Authentication
- **Page Access Tokens:** Meta distinguishes between User Access Tokens and Page Access Tokens. All Page management operations (feed posting, comment replies, photo uploads) require a Page Access Token with appropriate scopes (`pages_manage_posts`, `pages_manage_engagement`, `pages_read_engagement`).
- **Token Verification on Boot:** On initialization, `fastmcp-facebook` performs a lightweight call to `GET /{page-id}?fields=id,name` to ensure credentials are valid and active.

### B. Client-to-Server Authorization
- **Local Stdio Trust Model:** When executing over `stdio`, the MCP server runs under the identity of the invoking operating system user. Trust is derived from the operating system's process isolation.
- **Page Ownership Verification:** To prevent cross-page access attempts, the server queries `GET /me/accounts` to verify that the target `page_id` is within the set of Pages granted to the token before executing any tool operation.

---

## 3. The Two-Stage Publishing Security Contract

### Protocol Definition:
1. **Action Preparation:**
   ```python
   staged_action_id = hash(page_id + action_type + json(parameters) + salt)
   ```
   The record is stored in memory with an expiration timestamp ($TTL = 900\text{ seconds}$).
2. **Tamper-Proof Binding:**
   The client receives *only* the `staged_action_id` and a human-readable preview. The client cannot modify the post parameters during the second stage.
3. **Approval Execution:**
   When invoking `posts_publish_approved(staged_action_id, approval_token)`:
   - Check if `staged_action_id` exists in the active staging store.
   - Verify `current_time < expiration_time`.
   - Verify `staged_action.is_consumed == False`.
   - Mark `staged_action.is_consumed = True` immediately before initiating the HTTP request (atomic consumption).
   - If Meta returns an error, record the failure in the audit log.

---

## 4. Secret Sanitization & Redaction Engine

All outbound data streams are passed through the `SecretSanitizer`:

```python
class SecretSanitizer:
    def __init__(self, secrets: List[str]):
        self._secrets = [s for s in secrets if s and len(s) > 6]

    def redact(self, text: str) -> str:
        for secret in self._secrets:
            text = text.replace(secret, "[REDACTED_SECRET]")
        return text
```

This filter is applied to:
- Custom logging handlers writing to `stderr`.
- Exception messages serialized into MCP JSON-RPC error responses.
- HTTP debug logs and curl command representations.
