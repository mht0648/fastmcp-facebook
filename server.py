"""Custom Model Context Protocol (MCP) Server for Facebook Marketing."""

import sys
import json
import os
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

# Load local modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from meta_client import MetaGraphClient, MetaClientError
from copy_templates import format_marketing_copy, TEMPLATES


# Configure logging to stderr (stdio stdout is reserved for JSON-RPC messages)
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [MCP-Meta] %(levelname)s: %(message)s",
    stream=sys.stderr
)
logger = logging.getLogger("fastmcp_facebook")


def load_env_file(filepath: Optional[str] = None):
    """Simple zero-dependency .env loader."""
    if not filepath:
        # Check current directory and parent directory
        candidates = [
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env"),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"),
            os.path.join(os.getcwd(), ".env")
        ]
        for c in candidates:
            if os.path.exists(c):
                filepath = c
                break

    if filepath and os.path.exists(filepath):
        logger.info(f"Loading environment variables from {filepath}")
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                k = k.strip()
                v = v.strip().strip("'\"")
                if k and k not in os.environ:
                    os.environ[k] = v


# Load environment variables on startup
load_env_file()


TOOLS_DEFINITIONS: List[Dict[str, Any]] = [
    {
        "name": "verify_facebook_connection",
        "description": "Check if BabuJeeStore's Facebook Page connection and access token are valid.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "generate_product_post_copy",
        "description": "Generate high-converting Facebook product post copy with hooks, emojis, CTA, and hashtags.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "product_name": {
                    "type": "string",
                    "description": "The name/title of the product."
                },
                "price": {
                    "type": "string",
                    "description": "Price with currency symbol (e.g. '$24.99' or 'Rs. 2,999')."
                },
                "product_url": {
                    "type": "string",
                    "description": "The full link to the product on your website."
                },
                "description": {
                    "type": "string",
                    "description": "Short summary of key features or benefits."
                },
                "discount_percent": {
                    "type": "integer",
                    "description": "Optional percentage discount (e.g. 25 for 25% OFF)."
                },
                "style": {
                    "type": "string",
                    "enum": ["promotional", "new_arrival", "benefit_driven", "flash_sale"],
                    "description": "Copywriting angle. Defaults to 'promotional'."
                },
                "custom_hashtags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional additional hashtags."
                }
            },
            "required": ["product_name", "price", "product_url", "description"]
        }
    },
    {
        "name": "publish_facebook_post",
        "description": "Publish a status update or link post directly to the Facebook Page feed.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "The text copy/caption of the post."
                },
                "link": {
                    "type": "string",
                    "description": "Optional product or article link to preview in the post."
                }
            },
            "required": ["message"]
        }
    },
    {
        "name": "publish_facebook_photo",
        "description": "Publish a product photo with a caption to the Facebook Page feed. Supports image URLs or local files.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "caption": {
                    "type": "string",
                    "description": "Marketing caption accompanying the photo."
                },
                "image_url": {
                    "type": "string",
                    "description": "Public web URL of the product image."
                },
                "image_path": {
                    "type": "string",
                    "description": "Local file path to the image on disk."
                }
            },
            "required": ["caption"]
        }
    },
    {
        "name": "publish_facebook_carousel",
        "description": "Publish a multi-photo product showcase/carousel to the Facebook Page feed.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "caption": {
                    "type": "string",
                    "description": "Caption describing the product collection or promotion."
                },
                "photo_urls": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of 2 to 10 image web URLs to display in the post."
                }
            },
            "required": ["caption", "photo_urls"]
        }
    },
    {
        "name": "schedule_facebook_post",
        "description": "Schedule a text or photo post for future publication on Facebook Page (between 10 minutes and 75 days ahead).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "The caption or message."
                },
                "publish_timestamp": {
                    "type": "integer",
                    "description": "Unix timestamp in seconds for when the post should be published."
                },
                "image_url": {
                    "type": "string",
                    "description": "Optional image web URL if this is a photo post."
                },
                "link": {
                    "type": "string",
                    "description": "Optional website link if this is a link post."
                }
            },
            "required": ["message", "publish_timestamp"]
        }
    },
    {
        "name": "get_facebook_recent_posts",
        "description": "Retrieve recent posts with engagement metrics (reactions, comments, shares) to analyze marketing performance.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Number of posts to fetch (default: 5, max: 25)."
                }
            },
            "required": []
        }
    },
    {
        "name": "get_facebook_page_insights",
        "description": "Fetch Page impressions, reach, and user engagement metrics.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "period": {
                    "type": "string",
                    "enum": ["day", "week", "days_28"],
                    "description": "Reporting period (default: 'day')."
                }
            },
            "required": []
        }
    },
    {
        "name": "reply_to_facebook_comment",
        "description": "Reply to a customer's comment on a post with customer assistance or a direct product link.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "comment_id": {
                    "type": "string",
                    "description": "The ID of the comment to reply to."
                },
                "message": {
                    "type": "string",
                    "description": "The reply message."
                }
            },
            "required": ["comment_id", "message"]
        }
    }
]


def handle_tool_call(name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a specific MCP tool."""
    client = MetaGraphClient()

    if name == "verify_facebook_connection":
        return client.verify_credentials()

    elif name == "generate_product_post_copy":
        copy_text = format_marketing_copy(
            product_name=args["product_name"],
            price=args["price"],
            product_url=args["product_url"],
            description=args["description"],
            discount_percent=args.get("discount_percent"),
            style=args.get("style", "promotional"),
            custom_hashtags=args.get("custom_hashtags")
        )
        return {"generated_copy": copy_text, "style_used": args.get("style", "promotional")}

    elif name == "publish_facebook_post":
        return client.publish_post(
            message=args["message"],
            link=args.get("link")
        )

    elif name == "publish_facebook_photo":
        return client.publish_photo(
            caption=args["caption"],
            image_url=args.get("image_url"),
            image_path=args.get("image_path")
        )

    elif name == "publish_facebook_carousel":
        return client.publish_carousel(
            caption=args["caption"],
            photo_urls=args["photo_urls"]
        )

    elif name == "schedule_facebook_post":
        ts = args["publish_timestamp"]
        image_url = args.get("image_url")
        if image_url:
            return client.publish_photo(
                caption=args["message"],
                image_url=image_url,
                published=False,
                scheduled_publish_time=ts
            )
        else:
            return client.publish_post(
                message=args["message"],
                link=args.get("link"),
                published=False,
                scheduled_publish_time=ts
            )

    elif name == "get_facebook_recent_posts":
        limit = min(max(args.get("limit", 5), 1), 25)
        return client.get_recent_posts(limit=limit)

    elif name == "get_facebook_page_insights":
        period = args.get("period", "day")
        return client.get_page_insights(period=period)

    elif name == "reply_to_facebook_comment":
        return client.reply_to_comment(
            comment_id=args["comment_id"],
            message=args["message"]
        )

    else:
        raise ValueError(f"Unknown tool: {name}")


def process_json_rpc(line: str) -> Optional[Dict[str, Any]]:
    """Process incoming JSON-RPC 2.0 messages from stdio."""
    try:
        req = json.loads(line)
    except json.JSONDecodeError as e:
        return {
            "jsonrpc": "2.0",
            "id": None,
            "error": {"code": -32700, "message": f"Parse error: {str(e)}"}
        }

    msg_id = req.get("id")
    method = req.get("method")
    params = req.get("params", {})

    logger.debug(f"Received method: {method}")

    # Standard MCP handshake
    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "serverInfo": {
                    "name": "babujee-facebook-marketing-mcp",
                    "version": "1.0.0"
                }
            }
        }

    elif method in ("notifications/initialized", "initialized"):
        # Notifications don't return responses
        return None

    elif method == "ping":
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {}
        }

    elif method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {
                "tools": TOOLS_DEFINITIONS
            }
        }

    elif method == "tools/call":
        tool_name = params.get("name")
        tool_args = params.get("arguments", {})
        try:
            result_data = handle_tool_call(tool_name, tool_args)
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result_data, indent=2)
                        }
                    ],
                    "isError": False
                }
            }
        except MetaClientError as e:
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Meta Graph API Error: {str(e)}\nDetails: {json.dumps(e.fb_error)}"
                        }
                    ],
                    "isError": True
                }
            }
        except Exception as e:
            logger.exception("Error executing tool")
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Internal Error executing {tool_name}: {str(e)}"
                        }
                    ],
                    "isError": True
                }
            }

    else:
        if msg_id is not None:
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {
                    "code": -32601,
                    "message": f"Method '{method}' not found."
                }
            }
        return None


def main():
    """Main loop reading from stdin and writing to stdout."""
    logger.info("BabuJeeStore Facebook Marketing MCP Server started.")
    try:
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            response = process_json_rpc(line)
            if response is not None:
                sys.stdout.write(json.dumps(response) + "\n")
                sys.stdout.flush()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Shutting down MCP Server.")


if __name__ == "__main__":
    main()
