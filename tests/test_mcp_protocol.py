"""Contract and JSON-RPC 2.0 protocol tests for process_json_rpc in server.py."""

import unittest
from unittest.mock import patch
import json

from server import process_json_rpc, MetaClientError


class TestMCPProtocol(unittest.TestCase):
    """Test suite for MCP protocol compliance and JSON-RPC message handling."""

    # ---------------------------------------------------------
    # Protocol Handshake & System Methods
    # ---------------------------------------------------------
    def test_initialize_handshake(self):
        req = json.dumps({
            "jsonrpc": "2.0",
            "id": "req-1",
            "method": "initialize",
            "params": {"protocolVersion": "2024-11-05"}
        })
        res = process_json_rpc(req)
        self.assertEqual(res["jsonrpc"], "2.0")
        self.assertEqual(res["id"], "req-1")
        self.assertEqual(res["result"]["protocolVersion"], "2024-11-05")
        self.assertIn("tools", res["result"]["capabilities"])
        self.assertIn("name", res["result"]["serverInfo"])

    def test_initialized_notifications_return_none(self):
        for method in ("notifications/initialized", "initialized"):
            req = json.dumps({"jsonrpc": "2.0", "method": method})
            res = process_json_rpc(req)
            self.assertIsNone(res, f"Notification '{method}' should return None")

    def test_ping_method(self):
        req = json.dumps({"jsonrpc": "2.0", "id": 42, "method": "ping"})
        res = process_json_rpc(req)
        self.assertEqual(res["jsonrpc"], "2.0")
        self.assertEqual(res["id"], 42)
        self.assertEqual(res["result"], {})

    def test_tools_list(self):
        req = json.dumps({"jsonrpc": "2.0", "id": 100, "method": "tools/list", "params": {}})
        res = process_json_rpc(req)
        self.assertEqual(res["id"], 100)
        tools = res["result"]["tools"]
        self.assertIsInstance(tools, list)
        self.assertEqual(len(tools), 9)

    # ---------------------------------------------------------
    # Tool Invocation (tools/call) & Error Contracts
    # ---------------------------------------------------------
    @patch("server.handle_tool_call")
    def test_tools_call_success(self, mock_handle):
        mock_handle.return_value = {"status": "published", "post_id": "999"}
        req = json.dumps({
            "jsonrpc": "2.0",
            "id": "call-1",
            "method": "tools/call",
            "params": {
                "name": "publish_facebook_post",
                "arguments": {"message": "Test Message"}
            }
        })
        res = process_json_rpc(req)
        self.assertEqual(res["id"], "call-1")
        self.assertFalse(res["result"]["isError"])
        content = res["result"]["content"]
        self.assertEqual(len(content), 1)
        self.assertEqual(content[0]["type"], "text")
        parsed = json.loads(content[0]["text"])
        self.assertEqual(parsed["post_id"], "999")

    @patch("server.handle_tool_call")
    def test_tools_call_meta_client_error(self, mock_handle):
        mock_handle.side_effect = MetaClientError(
            "Access token expired",
            status_code=401,
            fb_error={"code": 190, "message": "Session expired"}
        )
        req = json.dumps({
            "jsonrpc": "2.0",
            "id": "call-err-1",
            "method": "tools/call",
            "params": {
                "name": "verify_facebook_connection",
                "arguments": {}
            }
        })
        res = process_json_rpc(req)
        self.assertEqual(res["id"], "call-err-1")
        self.assertTrue(res["result"]["isError"])
        text = res["result"]["content"][0]["text"]
        self.assertIn("Meta Graph API Error", text)
        self.assertIn("Access token expired", text)
        self.assertIn('"code": 190', text)

    @patch("server.handle_tool_call")
    def test_tools_call_unexpected_internal_error(self, mock_handle):
        mock_handle.side_effect = KeyError("missing_required_key")
        req = json.dumps({
            "jsonrpc": "2.0",
            "id": "call-err-2",
            "method": "tools/call",
            "params": {
                "name": "generate_product_post_copy",
                "arguments": {}
            }
        })
        res = process_json_rpc(req)
        self.assertEqual(res["id"], "call-err-2")
        self.assertTrue(res["result"]["isError"])
        text = res["result"]["content"][0]["text"]
        self.assertIn("Internal Error executing generate_product_post_copy", text)

    # ---------------------------------------------------------
    # JSON-RPC Error Handling
    # ---------------------------------------------------------
    def test_malformed_json_parse_error(self):
        bad_json = '{"jsonrpc": "2.0", "id": 1, "method": unquoted_string}'
        res = process_json_rpc(bad_json)
        self.assertEqual(res["jsonrpc"], "2.0")
        self.assertIsNone(res["id"])
        self.assertEqual(res["error"]["code"], -32700)
        self.assertIn("Parse error", res["error"]["message"])

    def test_unknown_method_with_id(self):
        req = json.dumps({
            "jsonrpc": "2.0",
            "id": 999,
            "method": "unknown_mcp_function",
            "params": {}
        })
        res = process_json_rpc(req)
        self.assertEqual(res["id"], 999)
        self.assertEqual(res["error"]["code"], -32601)
        self.assertIn("Method 'unknown_mcp_function' not found", res["error"]["message"])

    def test_unknown_notification_without_id(self):
        req = json.dumps({
            "jsonrpc": "2.0",
            "method": "custom/notification"
        })
        res = process_json_rpc(req)
        self.assertIsNone(res)


if __name__ == "__main__":
    unittest.main()
