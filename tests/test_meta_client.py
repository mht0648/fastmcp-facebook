"""Unit and mocked integration tests for meta_client.py."""

import unittest
from unittest.mock import patch, MagicMock, mock_open
import json
import urllib.error
import io

from meta_client import MetaGraphClient, MetaClientError, DEFAULT_GRAPH_VERSION


class TestMetaGraphClient(unittest.TestCase):
    """Test suite for Meta Graph API Client."""

    def setUp(self):
        self.page_id = "123456789"
        self.access_token = "EAAGtesttoken123"
        self.client = MetaGraphClient(
            page_id=self.page_id,
            access_token=self.access_token,
            api_version="v21.0"
        )

    # ---------------------------------------------------------
    # Initialization & Environment Configuration
    # ---------------------------------------------------------
    def test_init_with_explicit_args(self):
        client = MetaGraphClient(page_id="p1", access_token="t1", api_version="v20.0")
        self.assertEqual(client.page_id, "p1")
        self.assertEqual(client.access_token, "t1")
        self.assertEqual(client.api_version, "v20.0")

    @patch.dict("os.environ", {
        "FB_PAGE_ID": "env_page",
        "FB_PAGE_ACCESS_TOKEN": "env_token",
        "FB_API_VERSION": "v22.0"
    })
    def test_init_from_environment(self):
        client = MetaGraphClient()
        self.assertEqual(client.page_id, "env_page")
        self.assertEqual(client.access_token, "env_token")
        self.assertEqual(client.api_version, "v22.0")

    # ---------------------------------------------------------
    # verify_credentials
    # ---------------------------------------------------------
    def test_verify_credentials_missing_page_id(self):
        client = MetaGraphClient(page_id="", access_token="t1")
        with self.assertRaises(MetaClientError) as ctx:
            client.verify_credentials()
        self.assertIn("FB_PAGE_ID is not configured", str(ctx.exception))

    @patch.object(MetaGraphClient, "_make_request")
    def test_verify_credentials_success(self, mock_req):
        mock_req.return_value = {
            "id": "123456789",
            "name": "BabuJee Official",
            "link": "https://facebook.com/123456789",
            "fan_count": 5200,
            "is_published": True,
            "verification_status": "verified"
        }
        res = self.client.verify_credentials()
        self.assertEqual(res["status"], "connected")
        self.assertEqual(res["page_id"], "123456789")
        self.assertEqual(res["page_name"], "BabuJee Official")
        self.assertEqual(res["fans"], 5200)
        self.assertTrue(res["is_published"])

    # ---------------------------------------------------------
    # publish_post
    # ---------------------------------------------------------
    def test_publish_post_missing_page_id(self):
        client = MetaGraphClient(page_id="", access_token="token")
        with self.assertRaises(MetaClientError):
            client.publish_post(message="Hello World")

    @patch.object(MetaGraphClient, "_make_request")
    def test_publish_post_text_only(self, mock_req):
        mock_req.return_value = {"id": "123456789_111111"}
        res = self.client.publish_post(message="Brand new drop!")
        self.assertTrue(res["success"])
        self.assertEqual(res["post_id"], "123456789_111111")
        self.assertEqual(res["status"], "published")
        mock_req.assert_called_once_with(
            "/123456789/feed",
            method="POST",
            data={"message": "Brand new drop!", "published": "true"}
        )

    @patch.object(MetaGraphClient, "_make_request")
    def test_publish_post_scheduled_and_link(self, mock_req):
        mock_req.return_value = {"id": "123456789_222222"}
        ts = 1770000000
        res = self.client.publish_post(
            message="Check our deal!",
            link="https://example.com/deal",
            scheduled_publish_time=ts
        )
        self.assertEqual(res["status"], "scheduled")
        data = mock_req.call_args[1]["data"]
        self.assertEqual(data["published"], "false")
        self.assertEqual(data["link"], "https://example.com/deal")
        self.assertEqual(data["scheduled_publish_time"], str(ts))

    # ---------------------------------------------------------
    # publish_photo
    # ---------------------------------------------------------
    def test_publish_photo_no_url_or_path(self):
        with self.assertRaises(MetaClientError) as ctx:
            self.client.publish_photo(caption="Nice photo")
        self.assertIn("Must provide either image_url or image_path", str(ctx.exception))

    def test_publish_photo_nonexistent_local_file(self):
        with self.assertRaises(MetaClientError) as ctx:
            self.client.publish_photo(caption="Local photo", image_path="/nonexistent/photo.jpg")
        self.assertIn("Local file does not exist", str(ctx.exception))

    @patch.object(MetaGraphClient, "_make_request")
    def test_publish_photo_with_url(self, mock_req):
        mock_req.return_value = {"id": "photo_100", "post_id": "post_100"}
        res = self.client.publish_photo(caption="Summer Dress", image_url="https://example.com/dress.jpg")
        self.assertTrue(res["success"])
        self.assertEqual(res["photo_id"], "photo_100")
        self.assertEqual(res["post_id"], "post_100")
        self.assertEqual(res["status"], "published")

    @patch("os.path.exists", return_value=True)
    @patch.object(MetaGraphClient, "_make_request")
    def test_publish_photo_with_valid_local_path(self, mock_req, mock_exists):
        mock_req.return_value = {"id": "photo_200", "post_id": "post_200"}
        res = self.client.publish_photo(caption="Local Asset", image_path="/valid/path.png")
        self.assertTrue(res["success"])
        mock_req.assert_called_once_with(
            f"/{self.page_id}/photos",
            method="POST",
            data={"caption": "Local Asset", "published": "true"},
            files={"source": "/valid/path.png"}
        )

    # ---------------------------------------------------------
    # publish_carousel
    # ---------------------------------------------------------
    def test_publish_carousel_insufficient_photos(self):
        with self.assertRaises(MetaClientError) as ctx:
            self.client.publish_carousel(caption="Collection", photo_urls=["https://example.com/1.jpg"])
        self.assertIn("At least 2 photo URLs are required", str(ctx.exception))

    @patch.object(MetaGraphClient, "_make_request")
    def test_publish_carousel_success(self, mock_req):
        # 1st call: photo 1 upload, 2nd call: photo 2 upload, 3rd call: feed attach
        mock_req.side_effect = [
            {"id": "media_1"},
            {"id": "media_2"},
            {"id": "feed_post_999"}
        ]
        res = self.client.publish_carousel(
            caption="3-Piece Summer Suite",
            photo_urls=["https://example.com/1.jpg", "https://example.com/2.jpg"]
        )
        self.assertTrue(res["success"])
        self.assertEqual(res["post_id"], "feed_post_999")
        self.assertEqual(res["uploaded_photos_count"], 2)
        self.assertEqual(mock_req.call_count, 3)

    # ---------------------------------------------------------
    # get_recent_posts
    # ---------------------------------------------------------
    @patch.object(MetaGraphClient, "_make_request")
    def test_get_recent_posts(self, mock_req):
        mock_req.return_value = {
            "data": [
                {
                    "id": "post_1",
                    "message": "A" * 200,  # Should be truncated to 120 chars
                    "created_time": "2026-10-17T12:00:00Z",
                    "permalink_url": "https://fb.com/post_1",
                    "reactions": {"summary": {"total_count": 42}},
                    "comments": {"summary": {"total_count": 8}},
                    "shares": {"count": 3}
                },
                {
                    "id": "post_2",
                    "created_time": "2026-10-16T12:00:00Z"
                    # Missing comments, reactions, shares, message
                }
            ]
        }
        res = self.client.get_recent_posts(limit=2)
        self.assertEqual(res["total_retrieved"], 2)
        self.assertEqual(len(res["posts"]), 2)
        # Check truncation
        self.assertEqual(len(res["posts"][0]["message"]), 120)
        self.assertEqual(res["posts"][0]["reactions"], 42)
        self.assertEqual(res["posts"][0]["comments"], 8)
        self.assertEqual(res["posts"][0]["shares"], 3)
        # Check missing fields defaults
        self.assertEqual(res["posts"][1]["message"], "")
        self.assertEqual(res["posts"][1]["reactions"], 0)
        self.assertEqual(res["posts"][1]["comments"], 0)
        self.assertEqual(res["posts"][1]["shares"], 0)

    # ---------------------------------------------------------
    # get_page_insights
    # ---------------------------------------------------------
    @patch.object(MetaGraphClient, "_make_request")
    def test_get_page_insights(self, mock_req):
        mock_req.return_value = {
            "data": [
                {
                    "name": "page_impressions",
                    "title": "Daily Page Impressions",
                    "values": [{"value": 1500, "end_time": "2026-10-17T07:00:00+0000"}]
                },
                {
                    "name": "page_post_engagements",
                    "title": "Daily Post Engagements",
                    "values": []  # Empty values array edge case
                }
            ]
        }
        res = self.client.get_page_insights()
        insights = res["insights"]
        self.assertIn("page_impressions", insights)
        self.assertEqual(insights["page_impressions"]["latest_value"], 1500)
        self.assertIn("page_post_engagements", insights)
        self.assertIsNone(insights["page_post_engagements"]["latest_value"])

    # ---------------------------------------------------------
    # reply_to_comment
    # ---------------------------------------------------------
    @patch.object(MetaGraphClient, "_make_request")
    def test_reply_to_comment(self, mock_req):
        mock_req.return_value = {"id": "comment_reply_456"}
        res = self.client.reply_to_comment("comment_123", "Thank you for reaching out!")
        self.assertTrue(res["success"])
        self.assertEqual(res["comment_id"], "comment_reply_456")
        self.assertEqual(res["parent_id"], "comment_123")
        mock_req.assert_called_once_with(
            "/comment_123/comments",
            method="POST",
            data={"message": "Thank you for reaching out!"}
        )

    # ---------------------------------------------------------
    # exchange_token
    # ---------------------------------------------------------
    @patch("urllib.request.urlopen")
    def test_exchange_token_success(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({
            "access_token": "long_lived_token_xyz",
            "token_type": "bearer",
            "expires_in": 5184000
        }).encode("utf-8")
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        res = MetaGraphClient.exchange_token("short_token", "app_123", "secret_456")
        self.assertEqual(res["access_token"], "long_lived_token_xyz")
        self.assertEqual(res["expires_in"], 5184000)

    # ---------------------------------------------------------
    # _make_request & Low-Level HTTP Error Handling
    # ---------------------------------------------------------
    def test_make_request_missing_token_and_not_oauth(self):
        client = MetaGraphClient(page_id="p1", access_token="")
        with self.assertRaises(MetaClientError) as ctx:
            client._make_request("/me/accounts")
        self.assertIn("FB_PAGE_ACCESS_TOKEN is missing", str(ctx.exception))

    @patch("urllib.request.urlopen")
    def test_make_request_http_error_with_meta_json(self, mock_urlopen):
        error_payload = json.dumps({
            "error": {
                "message": "(#100) Param link must be a valid URL.",
                "type": "OAuthException",
                "code": 100
            }
        }).encode("utf-8")
        http_error = urllib.error.HTTPError(
            url="https://graph.facebook.com/v21.0/feed",
            code=400,
            msg="Bad Request",
            hdrs={},
            fp=io.BytesIO(error_payload)
        )
        mock_urlopen.side_effect = http_error

        with self.assertRaises(MetaClientError) as ctx:
            self.client._make_request("/feed", method="POST", data={"link": "bad-url"})
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("Param link must be a valid URL", str(ctx.exception))
        self.assertEqual(ctx.exception.fb_error["code"], 100)

    @patch("urllib.request.urlopen")
    def test_make_request_http_error_with_raw_html(self, mock_urlopen):
        http_error = urllib.error.HTTPError(
            url="https://graph.facebook.com/v21.0/feed",
            code=502,
            msg="Bad Gateway",
            hdrs={},
            fp=io.BytesIO(b"<html>502 Bad Gateway</html>")
        )
        mock_urlopen.side_effect = http_error

        with self.assertRaises(MetaClientError) as ctx:
            self.client._make_request("/feed")
        self.assertEqual(ctx.exception.status_code, 502)
        self.assertIn("HTTP Error 502", str(ctx.exception))

    @patch("urllib.request.urlopen")
    def test_make_request_network_url_error(self, mock_urlopen):
        url_error = urllib.error.URLError("Connection refused")
        mock_urlopen.side_effect = url_error

        with self.assertRaises(MetaClientError) as ctx:
            self.client._make_request("/feed")
        self.assertIn("Network error connecting to Meta Graph API", str(ctx.exception))

    @patch("urllib.request.urlopen")
    @patch("builtins.open", new_callable=mock_open, read_data=b"fake-image-bytes")
    def test_make_request_multipart_file_upload(self, mock_file, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({"id": "photo_uploaded_1"}).encode("utf-8")
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        res = self.client._make_request(
            "/photos",
            method="POST",
            data={"caption": "Test Photo"},
            files={"source": "test.png"}
        )
        self.assertEqual(res["id"], "photo_uploaded_1")
        req_arg = mock_urlopen.call_args[0][0]
        self.assertIn("multipart/form-data; boundary=", req_arg.headers["Content-type"])


if __name__ == "__main__":
    unittest.main()
