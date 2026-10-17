"""Unit and edge-case tests for MCP server tools in server.py."""

import unittest
from unittest.mock import patch, MagicMock
import tempfile
import os

from server import (
    load_env_file,
    handle_tool_call,
    TOOLS_DEFINITIONS,
    MetaClientError
)


class TestServerTools(unittest.TestCase):
    """Test suite for server tool dispatching, schema integrity, and execution."""

    def test_tools_definitions_schema_integrity(self):
        """Verify that all 9 tools follow the MCP tool specification."""
        self.assertEqual(len(TOOLS_DEFINITIONS), 9)
        names = set()
        for tool in TOOLS_DEFINITIONS:
            self.assertIn("name", tool)
            self.assertIn("description", tool)
            self.assertIn("inputSchema", tool)
            schema = tool["inputSchema"]
            self.assertEqual(schema["type"], "object")
            self.assertIsInstance(schema.get("properties"), dict)
            self.assertIsInstance(schema.get("required"), list)
            names.add(tool["name"])

        expected = {
            "verify_facebook_connection",
            "generate_product_post_copy",
            "publish_facebook_post",
            "publish_facebook_photo",
            "publish_facebook_carousel",
            "schedule_facebook_post",
            "get_facebook_recent_posts",
            "get_facebook_page_insights",
            "reply_to_facebook_comment"
        }
        self.assertEqual(names, expected)

    # ---------------------------------------------------------
    # load_env_file Tests
    # ---------------------------------------------------------
    def test_load_env_file_parsing(self):
        with tempfile.NamedTemporaryFile("w+", delete=False) as f:
            f.write("# Comment line\n")
            f.write("\n")
            f.write("TEST_ENV_VAR1=hello\n")
            f.write('TEST_ENV_VAR2="double_quoted_value"\n')
            f.write("TEST_ENV_VAR3='single_quoted_value'\n")
            f.write("MALFORMED_LINE_NO_EQUALS\n")
            temp_path = f.name

        try:
            load_env_file(temp_path)
            self.assertEqual(os.environ.get("TEST_ENV_VAR1"), "hello")
            self.assertEqual(os.environ.get("TEST_ENV_VAR2"), "double_quoted_value")
            self.assertEqual(os.environ.get("TEST_ENV_VAR3"), "single_quoted_value")
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            os.environ.pop("TEST_ENV_VAR1", None)
            os.environ.pop("TEST_ENV_VAR2", None)
            os.environ.pop("TEST_ENV_VAR3", None)

    # ---------------------------------------------------------
    # Tool Execution via handle_tool_call
    # ---------------------------------------------------------
    @patch("server.MetaGraphClient")
    def test_verify_facebook_connection(self, mock_client_cls):
        mock_instance = mock_client_cls.return_value
        mock_instance.verify_credentials.return_value = {"status": "connected", "page_name": "TestPage"}
        res = handle_tool_call("verify_facebook_connection", {})
        self.assertEqual(res["status"], "connected")
        self.assertEqual(res["page_name"], "TestPage")
        mock_instance.verify_credentials.assert_called_once()

    def test_generate_product_post_copy(self):
        res = handle_tool_call("generate_product_post_copy", {
            "product_name": "Air Cushion Sneakers",
            "price": "$69.99",
            "product_url": "https://example.com/sneakers",
            "description": "Breathable mesh upper with shock-absorbing sole.",
            "discount_percent": 15,
            "style": "flash_sale"
        })
        self.assertIn("generated_copy", res)
        self.assertEqual(res["style_used"], "flash_sale")
        self.assertIn("Air Cushion Sneakers", res["generated_copy"])
        self.assertIn("(15% OFF!)", res["generated_copy"])

    @patch("server.MetaGraphClient")
    def test_publish_facebook_post(self, mock_client_cls):
        mock_instance = mock_client_cls.return_value
        mock_instance.publish_post.return_value = {"success": True, "post_id": "111"}
        res = handle_tool_call("publish_facebook_post", {
            "message": "Exciting news!",
            "link": "https://example.com"
        })
        self.assertTrue(res["success"])
        mock_instance.publish_post.assert_called_once_with(
            message="Exciting news!",
            link="https://example.com"
        )

    @patch("server.MetaGraphClient")
    def test_publish_facebook_photo(self, mock_client_cls):
        mock_instance = mock_client_cls.return_value
        mock_instance.publish_photo.return_value = {"success": True, "photo_id": "222"}
        res = handle_tool_call("publish_facebook_photo", {
            "caption": "Look at this view",
            "image_url": "https://example.com/view.jpg"
        })
        self.assertTrue(res["success"])
        mock_instance.publish_photo.assert_called_once_with(
            caption="Look at this view",
            image_url="https://example.com/view.jpg",
            image_path=None
        )

    @patch("server.MetaGraphClient")
    def test_publish_facebook_carousel(self, mock_client_cls):
        mock_instance = mock_client_cls.return_value
        mock_instance.publish_carousel.return_value = {"success": True, "post_id": "333"}
        res = handle_tool_call("publish_facebook_carousel", {
            "caption": "Showcase",
            "photo_urls": ["https://example.com/1.jpg", "https://example.com/2.jpg"]
        })
        self.assertTrue(res["success"])
        mock_instance.publish_carousel.assert_called_once_with(
            caption="Showcase",
            photo_urls=["https://example.com/1.jpg", "https://example.com/2.jpg"]
        )

    @patch("server.MetaGraphClient")
    def test_schedule_facebook_post_text(self, mock_client_cls):
        mock_instance = mock_client_cls.return_value
        mock_instance.publish_post.return_value = {"success": True, "status": "scheduled"}
        res = handle_tool_call("schedule_facebook_post", {
            "message": "Future Post",
            "publish_timestamp": 1780000000,
            "link": "https://example.com"
        })
        self.assertEqual(res["status"], "scheduled")
        mock_instance.publish_post.assert_called_once_with(
            message="Future Post",
            link="https://example.com",
            published=False,
            scheduled_publish_time=1780000000
        )

    @patch("server.MetaGraphClient")
    def test_schedule_facebook_post_photo(self, mock_client_cls):
        mock_instance = mock_client_cls.return_value
        mock_instance.publish_photo.return_value = {"success": True, "status": "scheduled"}
        res = handle_tool_call("schedule_facebook_post", {
            "message": "Future Photo Post",
            "publish_timestamp": 1780000000,
            "image_url": "https://example.com/future.jpg"
        })
        self.assertEqual(res["status"], "scheduled")
        mock_instance.publish_photo.assert_called_once_with(
            caption="Future Photo Post",
            image_url="https://example.com/future.jpg",
            published=False,
            scheduled_publish_time=1780000000
        )

    # ---------------------------------------------------------
    # get_facebook_recent_posts & Edge-case Limit Clamping
    # ---------------------------------------------------------
    @patch("server.MetaGraphClient")
    def test_get_facebook_recent_posts_limit_clamping(self, mock_client_cls):
        mock_instance = mock_client_cls.return_value
        mock_instance.get_recent_posts.return_value = {"total_retrieved": 0, "posts": []}

        # Case 1: Default limit when not provided (should be 5)
        handle_tool_call("get_facebook_recent_posts", {})
        mock_instance.get_recent_posts.assert_called_with(limit=5)

        # Case 2: Zero or negative limit should clamp to minimum 1
        handle_tool_call("get_facebook_recent_posts", {"limit": 0})
        mock_instance.get_recent_posts.assert_called_with(limit=1)

        handle_tool_call("get_facebook_recent_posts", {"limit": -10})
        mock_instance.get_recent_posts.assert_called_with(limit=1)

        # Case 3: Oversized limit should clamp to maximum 25
        handle_tool_call("get_facebook_recent_posts", {"limit": 100})
        mock_instance.get_recent_posts.assert_called_with(limit=25)

        # Case 4: Valid in-range limit
        handle_tool_call("get_facebook_recent_posts", {"limit": 15})
        mock_instance.get_recent_posts.assert_called_with(limit=15)

    @patch("server.MetaGraphClient")
    def test_get_facebook_page_insights(self, mock_client_cls):
        mock_instance = mock_client_cls.return_value
        mock_instance.get_page_insights.return_value = {"insights": {}}

        # Default period 'day'
        handle_tool_call("get_facebook_page_insights", {})
        mock_instance.get_page_insights.assert_called_with(period="day")

        # Explicit period 'week'
        handle_tool_call("get_facebook_page_insights", {"period": "week"})
        mock_instance.get_page_insights.assert_called_with(period="week")

    @patch("server.MetaGraphClient")
    def test_reply_to_facebook_comment(self, mock_client_cls):
        mock_instance = mock_client_cls.return_value
        mock_instance.reply_to_comment.return_value = {"success": True, "comment_id": "c99"}
        res = handle_tool_call("reply_to_facebook_comment", {
            "comment_id": "c123",
            "message": "Thanks for your order!"
        })
        self.assertTrue(res["success"])
        mock_instance.reply_to_comment.assert_called_once_with(
            comment_id="c123",
            message="Thanks for your order!"
        )

    def test_unknown_tool_call(self):
        with self.assertRaises(ValueError) as ctx:
            handle_tool_call("non_existent_tool", {})
        self.assertIn("Unknown tool: non_existent_tool", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
