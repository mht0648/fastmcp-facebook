# ADR-003: Two-Stage Controlled Publishing Workflow

## Status
Accepted

## Context
Exposing direct state-modifying tools (`publish_facebook_post`, `publish_facebook_photo`) to an autonomous AI agent introduces severe enterprise risks:
1. LLMs hallucinate arguments.
2. Cascading reasoning loops can generate unwanted spam.
3. Prompt injection within user-submitted comments can force the AI to issue unauthorized posts.

## Decision
All state-modifying operations are split into a mandatory two-stage workflow:
1. `posts_prepare`: Creates a staged action record, computes an SHA-256 fingerprint, and returns a short-lived `staged_action_id` (TTL: 15 minutes).
2. `posts_publish_approved`: Requires the `staged_action_id` and a valid approval token. It retrieves the exact frozen parameters from memory, consumes the token atomically, and posts to Meta.

## Rationale
1. **Human-in-the-Loop Guarantee:** The AI cannot authorize its own live post. The human operator must review the staged preview and supply confirmation.
2. **Tamper Prevention:** The execution tool does not accept post content or URLs—only the `staged_action_id`. This prevents the agent from changing the post between review and publication.
3. **Replay Defense:** The approval record is marked `consumed=True` immediately upon execution, preventing accidental double-posting.

## Consequences
- Requires an in-memory `StagedActionStore` (and Redis/DB for future distributed deployments).
- Requires a two-step conversational flow between the user and AI agent.
