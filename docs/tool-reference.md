# MCP Tool Reference: fastmcp-facebook

This document is the definitive specification for all tools exposed by `fastmcp-facebook`.

---

## Tool Catalog Summary

| Tool Name | Operation Mode | Input Schema | Output Schema | Security Class |
| :--- | :---: | :--- | :--- | :---: |
| `pages_verify_connection` | Read | Empty `{}` | `PageConnectionStatus` | Read |
| `pages_list` | Read | Empty `{}` | `PageSummaryList` | Read |
| `posts_list` | Read | `PostListRequest` | `PostSummaryList` | Read |
| `posts_prepare` | Staging | `PostPrepareRequest` | `StagedActionPreview` | Staging |
| `posts_publish_approved` | Write | `PostPublishRequest` | `PublishResult` | Sensitive Write |
| `comments_list` | Read | `CommentListRequest` | `CommentSummaryList` | Read |
| `comments_prepare_reply` | Staging | `CommentReplyPrepareRequest` | `StagedActionPreview` | Staging |
| `comments_publish_approved_reply` | Write | `CommentReplyPublishRequest` | `PublishResult` | Sensitive Write |
| `pages_get_insights` | Read | `PageInsightsRequest` | `InsightsSummary` | Read |

---

## 1. `pages_verify_connection`
- **Purpose:** Checks if the configured `FB_PAGE_ID` and `FB_PAGE_ACCESS_TOKEN` are active and can successfully connect to the Meta Graph API.
- **Side Effects:** None.
- **Input Parameters:** None.
- **Example Response:**
  ```json
  {
    "status": "connected",
    "page_id": "109823471029384",
    "page_name": "Acme Innovations",
    "page_url": "https://www.facebook.com/109823471029384",
    "fan_count": 1420,
    "is_published": true
  }
  ```

---

## 2. `posts_prepare`
- **Purpose:** Stages a draft post (text, link preview, or photos) for review, validating constraints locally and returning a secure `staged_action_id`.
- **Side Effects:** Generates an in-memory staging record with a 15-minute TTL. Does not publish to Facebook.
- **Input Parameters:**
  - `page_id` *(string, required)*: The target Facebook Page ID.
  - `message` *(string, required)*: Post body/caption (max 63,206 characters).
  - `link` *(string, optional)*: URL to preview in the post.
  - `scheduled_publish_time` *(integer, optional)*: Unix timestamp for scheduled publication.
- **Example Response:**
  ```json
  {
    "staged_action_id": "act_8f9a2b1c4e",
    "action_type": "publish_feed_post",
    "page_id": "109823471029384",
    "expires_in_seconds": 900,
    "preview": {
      "message": "Excited to announce our new product line!",
      "link": "https://example.com/new-line"
    },
    "instruction": "Present this staged_action_id to human reviewer. Provide approval_token to execute posts_publish_approved."
  }
  ```

---

## 3. `posts_publish_approved`
- **Purpose:** Publishes a previously staged post after receiving human verification.
- **Side Effects:** Creates a public post on the target Facebook Page feed. Burns the single-use `staged_action_id`.
- **Input Parameters:**
  - `staged_action_id` *(string, required)*: The ID returned by `posts_prepare`.
  - `approval_token` *(string, required)*: The verification nonce confirming human sign-off.
- **Example Response:**
  ```json
  {
    "success": true,
    "post_id": "109823471029384_987654321012345",
    "url": "https://www.facebook.com/109823471029384/posts/987654321012345",
    "published_at": "2026-10-17T18:30:00Z"
  }
  ```

---

## 4. `comments_list`
- **Purpose:** Ingests comments for a given post ID with prompt-injection defense tags.
- **Side Effects:** None.
- **Input Parameters:**
  - `post_id` *(string, required)*: The target post ID.
  - `limit` *(integer, optional)*: Number of comments to retrieve (default: 10, max: 50).
- **Security Feature:** All user comment strings are wrapped in `<untrusted_content>` delimiters with metadata (sentiment, author name, timestamp).
