# Security Policy: facebook-pages-mcp

## Reporting Security Vulnerabilities

The `facebook-pages-mcp` project prioritizes security above convenience and functionality.

If you discover a security vulnerability—especially concerning **credential leakage**, **cross-page authorization bypasses**, **prompt-injection execution**, or **two-stage approval tampering**—please report it responsibly.

**DO NOT create a public GitHub issue.**

Please report vulnerabilities privately by emailing:  
📧 **mht0648@gmail.com**

Please include:
1. Description of the vulnerability.
2. Steps to reproduce or proof-of-concept payload.
3. Potential impact and attack scenario.

We will acknowledge receipt within 48 hours and work with you on a coordinated disclosure timeline.

---

## Security Invariants

Our codebase enforces the following architectural invariants:
1. **Zero Secret Leakage:** Tokens and secrets are scrubbed at the transport layer and must never appear in logs, exceptions, or tool outputs.
2. **Two-Stage Write Approvals:** No write action (posting, replying, hiding) may execute without presenting an active, unconsumed human approval token.
3. **Prompt Injection Containment:** User-generated comments are always tagged as untrusted content and delimited before presentation to an AI agent.
