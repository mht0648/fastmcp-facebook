# Meta Graph API Permission & Capability Matrix (v21.0)

This matrix maps every supported and planned capability in `fastmcp-facebook` to its official Meta Graph API v21.0 endpoint, HTTP method, required permission scope, and App Review requirements.

---

## 1. Permission Matrix

| Operation | Graph API Endpoint | HTTP Method | Required Permission Scopes | App Review Required (Production) | Feasibility Status |
| :--- | :--- | :---: | :--- | :---: | :---: |
| **Verify Connection** | `/{page-id}` | `GET` | `pages_read_engagement` or `pages_show_list` | Yes | ✅ Supported |
| **List User's Pages** | `/me/accounts` | `GET` | `pages_show_list` | Yes | ✅ Supported |
| **Get Page Metadata** | `/{page-id}` | `GET` | `pages_read_engagement` | Yes | ✅ Supported |
| **List Page Posts** | `/{page-id}/posts` | `GET` | `pages_read_engagement`, `pages_read_user_content` | Yes | ✅ Supported |
| **Publish Text / Link Post** | `/{page-id}/feed` | `POST` | `pages_manage_posts` | Yes | ✅ Supported |
| **Publish Photo Post** | `/{page-id}/photos` | `POST` | `pages_manage_posts` | Yes | ✅ Supported |
| **Schedule Post** | `/{page-id}/feed` | `POST` | `pages_manage_posts` | Yes | ✅ Supported |
| **List Post Comments** | `/{post-id}/comments` | `GET` | `pages_read_user_content`, `pages_read_engagement` | Yes | ✅ Supported |
| **Reply to Comment** | `/{comment-id}/comments` | `POST` | `pages_manage_engagement` or `pages_manage_posts` | Yes | ✅ Supported |
| **Hide / Unhide Comment** | `/{comment-id}` | `POST` | `pages_manage_engagement` | Yes | ✅ Supported |
| **Page Insights** | `/{page-id}/insights` | `GET` | `read_insights`, `pages_read_engagement` | Yes | ✅ Supported |
| *Publish to Personal Profile*| `/me/feed` | `POST` | N/A | N/A | ❌ **Deprecated / Disallowed** |
| *Publish to Facebook Group* | `/{group-id}/feed` | `POST` | N/A | N/A | ❌ **Deprecated / Disallowed** |

---

## 2. Meta App Modes: Development vs Live

### Development Mode (Local Testing)
- **Permissions:** Any permission listed above can be used immediately without Meta App Review.
- **Audience Limitation:** The server can only interact with Pages owned or administered by users explicitly listed as **Administrators**, **Developers**, or **Testers** in your Meta App Dashboard.

### Live Mode (Production Deployment)
- **Business Verification:** Requires Meta Business Account verification.
- **App Review:** Each permission scope (`pages_manage_posts`, `pages_read_user_content`, `pages_read_engagement`, `read_insights`) must be submitted with a recorded video screencast demonstrating the application's user interface and business rationale.
