"""Meta Graph API Client for Facebook Page automation."""

import json
import os
import mimetypes
import urllib.request
import urllib.parse
import urllib.error
from typing import Dict, Any, Optional, List, Union


DEFAULT_GRAPH_VERSION = "v21.0"
BASE_URL = "https://graph.facebook.com"


class MetaClientError(Exception):
    """Custom exception for Meta Graph API errors."""
    def __init__(self, message: str, status_code: Optional[int] = None, fb_error: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.status_code = status_code
        self.fb_error = fb_error or {}


class MetaGraphClient:
    """Client for interacting with the Facebook Graph API without external dependencies."""

    def __init__(
        self,
        page_id: Optional[str] = None,
        access_token: Optional[str] = None,
        api_version: Optional[str] = None
    ):
        self.page_id = page_id or os.getenv("FB_PAGE_ID", "").strip()
        self.access_token = access_token or os.getenv("FB_PAGE_ACCESS_TOKEN", "").strip()
        self.api_version = api_version or os.getenv("FB_API_VERSION", DEFAULT_GRAPH_VERSION).strip()

    def _make_request(
        self,
        endpoint: str,
        method: str = "GET",
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Execute HTTP request against the Meta Graph API."""
        if not self.access_token and "oauth" not in endpoint:
            raise MetaClientError("FB_PAGE_ACCESS_TOKEN is missing. Please configure it in your environment.")

        # Ensure endpoint starts with slash and includes API version
        if not endpoint.startswith("/"):
            endpoint = f"/{endpoint}"
        if not endpoint.startswith(f"/{self.api_version}"):
            endpoint = f"/{self.api_version}{endpoint}"

        url = f"{BASE_URL}{endpoint}"

        query_params = dict(params or {})
        if self.access_token and "access_token" not in query_params:
            query_params["access_token"] = self.access_token

        if files:
            # Handle multipart/form-data for local file uploads
            boundary = f"----WebKitFormBoundary{os.urandom(16).hex()}"
            body_bytes = bytearray()

            # Merge data into multipart fields
            combined_fields = dict(query_params)
            if data:
                combined_fields.update(data)

            for key, val in combined_fields.items():
                if val is not None:
                    body_bytes.extend(f"--{boundary}\r\n".encode("utf-8"))
                    body_bytes.extend(f'Content-Disposition: form-data; name="{key}"\r\n\r\n'.encode("utf-8"))
                    body_bytes.extend(f"{val}\r\n".encode("utf-8"))

            for field_name, file_path in files.items():
                filename = os.path.basename(file_path)
                mime_type = mimetypes.guess_type(file_path)[0] or "application/octet-stream"
                with open(file_path, "rb") as f:
                    file_content = f.read()
                body_bytes.extend(f"--{boundary}\r\n".encode("utf-8"))
                body_bytes.extend(
                    f'Content-Disposition: form-data; name="{field_name}"; filename="{filename}"\r\n'.encode("utf-8")
                )
                body_bytes.extend(f"Content-Type: {mime_type}\r\n\r\n".encode("utf-8"))
                body_bytes.extend(file_content)
                body_bytes.extend(b"\r\n")

            body_bytes.extend(f"--{boundary}--\r\n".encode("utf-8"))

            req = urllib.request.Request(url, data=bytes(body_bytes), method=method)
            req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")

        elif method in ("POST", "PUT", "DELETE"):
            post_data = dict(data or {})
            # If query params present, include access token in post payload
            if "access_token" not in post_data and self.access_token:
                post_data["access_token"] = self.access_token
            encoded_data = urllib.parse.urlencode(post_data).encode("utf-8")
            req = urllib.request.Request(url, data=encoded_data, method=method)
            req.add_header("Content-Type", "application/x-www-form-urlencoded")
        else:
            if query_params:
                url = f"{url}?{urllib.parse.urlencode(query_params)}"
            req = urllib.request.Request(url, method=method)

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                resp_data = resp.read().decode("utf-8")
                return json.loads(resp_data)
        except urllib.error.HTTPError as e:
            try:
                error_body = json.loads(e.read().decode("utf-8"))
                fb_error = error_body.get("error", {})
                msg = f"Meta API Error ({e.code}): {fb_error.get('message', str(e))}"
                raise MetaClientError(msg, status_code=e.code, fb_error=fb_error) from e
            except json.JSONDecodeError:
                raise MetaClientError(f"HTTP Error {e.code}: {e.reason}", status_code=e.code) from e
        except urllib.error.URLError as e:
            raise MetaClientError(f"Network error connecting to Meta Graph API: {e.reason}") from e

    def verify_credentials(self) -> Dict[str, Any]:
        """Verify the configured Page ID and Access Token."""
        if not self.page_id:
            raise MetaClientError("FB_PAGE_ID is not configured.")
        endpoint = f"/{self.page_id}"
        params = {"fields": "id,name,link,fan_count,is_published,verification_status"}
        res = self._make_request(endpoint, method="GET", params=params)
        return {
            "status": "connected",
            "page_id": res.get("id"),
            "page_name": res.get("name"),
            "page_url": res.get("link"),
            "fans": res.get("fan_count", 0),
            "is_published": res.get("is_published", False)
        }

    def publish_post(
        self,
        message: str,
        link: Optional[str] = None,
        published: bool = True,
        scheduled_publish_time: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Publish or schedule a text/link status update to the Facebook Page feed.
        
        Args:
            message: Post copy / caption.
            link: Optional URL to preview in the post.
            published: If False, post is held as draft or scheduled.
            scheduled_publish_time: Unix timestamp for future publication (must be 10m to 75d in advance).
        """
        if not self.page_id:
            raise MetaClientError("FB_PAGE_ID is not configured.")
        endpoint = f"/{self.page_id}/feed"
        payload: Dict[str, Any] = {
            "message": message,
            "published": "true" if published else "false"
        }
        if link:
            payload["link"] = link
        if scheduled_publish_time:
            payload["published"] = "false"
            payload["scheduled_publish_time"] = str(scheduled_publish_time)

        res = self._make_request(endpoint, method="POST", data=payload)
        return {
            "success": True,
            "post_id": res.get("id"),
            "status": "scheduled" if scheduled_publish_time else "published"
        }

    def publish_photo(
        self,
        caption: str,
        image_url: Optional[str] = None,
        image_path: Optional[str] = None,
        published: bool = True,
        scheduled_publish_time: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Publish or schedule a photo post with caption to the Facebook Page.
        Provide either image_url (web link) or image_path (local file).
        """
        if not self.page_id:
            raise MetaClientError("FB_PAGE_ID is not configured.")
        if not image_url and not image_path:
            raise MetaClientError("Must provide either image_url or image_path.")

        endpoint = f"/{self.page_id}/photos"
        payload: Dict[str, Any] = {
            "caption": caption,
            "published": "true" if published else "false"
        }
        if scheduled_publish_time:
            payload["published"] = "false"
            payload["scheduled_publish_time"] = str(scheduled_publish_time)

        files = None
        if image_path:
            if not os.path.exists(image_path):
                raise MetaClientError(f"Local file does not exist: {image_path}")
            files = {"source": image_path}
        else:
            payload["url"] = image_url

        res = self._make_request(endpoint, method="POST", data=payload, files=files)
        return {
            "success": True,
            "photo_id": res.get("id"),
            "post_id": res.get("post_id"),
            "status": "scheduled" if scheduled_publish_time else "published"
        }

    def publish_carousel(
        self,
        caption: str,
        photo_urls: List[str]
    ) -> Dict[str, Any]:
        """
        Publish a multi-photo post (product showcase) using unpublished photos.
        """
        if not self.page_id:
            raise MetaClientError("FB_PAGE_ID is not configured.")
        if not photo_urls or len(photo_urls) < 2:
            raise MetaClientError("At least 2 photo URLs are required for a multi-photo showcase.")

        media_ids = []
        for url in photo_urls:
            # Upload photo as unpublished
            res = self._make_request(
                f"/{self.page_id}/photos",
                method="POST",
                data={"url": url, "published": "false"}
            )
            media_ids.append(res.get("id"))

        # Attach all uploaded photos to a single feed post
        attached_media = [{"media_fbid": str(mid)} for mid in media_ids]
        payload = {
            "message": caption,
            "attached_media": json.dumps(attached_media)
        }
        feed_res = self._make_request(f"/{self.page_id}/feed", method="POST", data=payload)
        return {
            "success": True,
            "post_id": feed_res.get("id"),
            "uploaded_photos_count": len(media_ids)
        }

    def get_recent_posts(self, limit: int = 10) -> Dict[str, Any]:
        """Retrieve recent posts and engagement metrics."""
        if not self.page_id:
            raise MetaClientError("FB_PAGE_ID is not configured.")
        endpoint = f"/{self.page_id}/posts"
        params = {
            "fields": "id,message,created_time,permalink_url,shares,comments.summary(true),reactions.summary(true)",
            "limit": str(limit)
        }
        res = self._make_request(endpoint, method="GET", params=params)
        posts = []
        for item in res.get("data", []):
            comments_count = item.get("comments", {}).get("summary", {}).get("total_count", 0)
            reactions_count = item.get("reactions", {}).get("summary", {}).get("total_count", 0)
            shares_count = item.get("shares", {}).get("count", 0)
            posts.append({
                "id": item.get("id"),
                "message": item.get("message", "")[:120],
                "created_time": item.get("created_time"),
                "url": item.get("permalink_url"),
                "reactions": reactions_count,
                "comments": comments_count,
                "shares": shares_count
            })
        return {"total_retrieved": len(posts), "posts": posts}

    def get_page_insights(
        self,
        metrics: Optional[List[str]] = None,
        period: str = "day"
    ) -> Dict[str, Any]:
        """
        Fetch Page engagement insights (impressions, post clicks, reactions).
        """
        if not self.page_id:
            raise MetaClientError("FB_PAGE_ID is not configured.")
        if not metrics:
            metrics = [
                "page_impressions",
                "page_impressions_unique",
                "page_post_engagements"
            ]
        endpoint = f"/{self.page_id}/insights"
        params = {
            "metric": ",".join(metrics),
            "period": period
        }
        res = self._make_request(endpoint, method="GET", params=params)
        parsed = {}
        for item in res.get("data", []):
            metric_name = item.get("name")
            values = item.get("values", [])
            latest = values[-1] if values else {}
            parsed[metric_name] = {
                "latest_value": latest.get("value"),
                "end_time": latest.get("end_time"),
                "title": item.get("title")
            }
        return {"insights": parsed}

    def reply_to_comment(self, comment_id: str, message: str) -> Dict[str, Any]:
        """Reply to a user comment on a post with a message or checkout link."""
        endpoint = f"/{comment_id}/comments"
        res = self._make_request(endpoint, method="POST", data={"message": message})
        return {
            "success": True,
            "comment_id": res.get("id"),
            "parent_id": comment_id
        }

    @staticmethod
    def exchange_token(user_access_token: str, app_id: str, app_secret: str) -> Dict[str, Any]:
        """
        Exchange a short-lived user token for a 60-day long-lived token.
        """
        url = f"{BASE_URL}/{DEFAULT_GRAPH_VERSION}/oauth/access_token"
        params = {
            "grant_type": "fb_exchange_token",
            "client_id": app_id,
            "client_secret": app_secret,
            "fb_exchange_token": user_access_token
        }
        full_url = f"{url}?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(full_url, method="GET")
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data
