#!/usr/bin/env python3
"""
Test script for BabuJeeStore Facebook MCP Server and Meta Graph API Client.
Usage:
    python3 fastmcp_facebook/test_client.py copy
    python3 fastmcp_facebook/test_client.py verify
    python3 fastmcp_facebook/test_client.py exchange-token <user_token> <app_id> <app_secret>
"""

import sys
import os
import json

# Ensure fastmcp_facebook is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from server import load_env_file, process_json_rpc
from meta_client import MetaGraphClient, MetaClientError
from copy_templates import format_marketing_copy


def test_copy_generation():
    print("=== Testing Marketing Copy Formatter ===")
    sample_copy = format_marketing_copy(
        product_name="Premium Leather Wallet",
        price="$34.99",
        product_url="https://babujeestore.com/products/leather-wallet",
        description="Crafted from 100% genuine top-grain leather with RFID blocking technology.",
        discount_percent=20,
        style="promotional",
        custom_hashtags=["#MensFashion", "#LeatherGoods"]
    )
    print("\n--- Promotional Style ---")
    print(sample_copy)
    
    print("\n--- Flash Sale Style ---")
    print(format_marketing_copy(
        product_name="Wireless Noise Cancelling Earbuds",
        price="$49.00",
        product_url="https://babujeestore.com/products/earbuds",
        description="Crystal clear audio with 36-hour battery life and fast charging.",
        discount_percent=35,
        style="flash_sale"
    ))
    print("\n[OK] Copy generation passed.")


def test_mcp_json_rpc():
    print("\n=== Testing MCP JSON-RPC Handshake ===")
    
    # 1. Initialize
    init_req = json.dumps({
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {"protocolVersion": "2024-11-05"}
    })
    init_res = process_json_rpc(init_req)
    assert init_res["result"]["serverInfo"]["name"] == "babujee-facebook-marketing-mcp"
    print("1. Initialize handshake: OK")
    
    # 2. Tools list
    tools_req = json.dumps({
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list",
        "params": {}
    })
    tools_res = process_json_rpc(tools_req)
    tools = tools_res["result"]["tools"]
    print(f"2. Tools list: {len(tools)} tools registered: {[t['name'] for t in tools]}")
    
    # 3. Test generate_product_post_copy tool call through MCP
    call_req = json.dumps({
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {
            "name": "generate_product_post_copy",
            "arguments": {
                "product_name": "Smart Fitness Watch",
                "price": "$59.99",
                "product_url": "https://babujeestore.com/products/fitness-watch",
                "description": "Track your heart rate, sleep, and workouts in real time.",
                "style": "new_arrival"
            }
        }
    })
    call_res = process_json_rpc(call_req)
    assert call_res["result"]["isError"] is False
    print("3. Tool execution (generate_product_post_copy): OK")
    print("[OK] MCP Protocol verification passed.")


def test_meta_connection():
    print("\n=== Testing Facebook Page Connection ===")
    load_env_file()
    page_id = os.getenv("FB_PAGE_ID")
    token = os.getenv("FB_PAGE_ACCESS_TOKEN")
    
    if not page_id or not token:
        print("[!] FB_PAGE_ID or FB_PAGE_ACCESS_TOKEN not set in environment or .env file.")
        print("    Configure your .env file to test live Meta Graph API calls.")
        return

    try:
        client = MetaGraphClient()
        info = client.verify_credentials()
        print(f"[OK] Successfully connected to Facebook Page: {info['page_name']} (ID: {info['page_id']})")
        print(f"     Page URL: {info['page_url']}")
        print(f"     Followers/Fans: {info['fans']}")
    except MetaClientError as e:
        print(f"[ERROR] Failed to verify connection: {e}")


def exchange_token(args):
    if len(args) < 3:
        print("Usage: python3 mcp_facebook/test_client.py exchange-token <user_token> <app_id> <app_secret>")
        return
    user_token, app_id, app_secret = args[0], args[1], args[2]
    print(f"Exchanging user token for long-lived token via Meta App {app_id}...")
    try:
        res = MetaGraphClient.exchange_token(user_token, app_id, app_secret)
        print("\n[OK] Successfully exchanged token!")
        print(f"Long-lived User Token:\n{res.get('access_token')}")
        print(f"Expires in: {res.get('expires_in', 'N/A')} seconds (~60 days)")
        print("\nNext: To obtain a PERMANENT Page Access Token, query:")
        print(f"GET https://graph.facebook.com/v21.0/me/accounts?access_token={res.get('access_token')}")
    except Exception as e:
        print(f"[ERROR] Token exchange failed: {e}")


if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else "all"
    if action == "copy":
        test_copy_generation()
    elif action == "verify":
        test_meta_connection()
    elif action == "exchange-token":
        exchange_token(sys.argv[2:])
    elif action == "all":
        test_copy_generation()
        test_mcp_json_rpc()
        test_meta_connection()
    else:
        print(f"Unknown command: {action}")
