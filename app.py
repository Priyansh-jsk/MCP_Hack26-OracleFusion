# app.py (improved)
import os
import sys
import base64
import json
import logging
from typing import Optional
from urllib.parse import quote_plus
import httpx
from mcp.server.fastmcp import FastMCP

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger("fusion-mcp")

mcp = FastMCP("mcpServer_fusion")

BASE_URL = os.getenv("ORACLE_FUSION_BASE_URL")
USERNAME = os.getenv("ORACLE_FUSION_USERNAME")
PASSWORD = os.getenv("ORACLE_FUSION_PASSWORD")
OAUTH = os.getenv("ORACLE_FUSION_OAUTH_TOKEN")

# MCP launcher logs show startup info
print("Starting app.py for Oracle Fusion MCP...", file=sys.stderr)
print(f"BASE_URL set? {'yes' if BASE_URL else 'no'}", file=sys.stderr)

def build_auth_headers():
    """
    Build auth headers. Raises ValueError if no auth configured.
    """
    if OAUTH:
        return {"Authorization": f"Bearer {OAUTH}"}
    elif USERNAME and PASSWORD:
        token = base64.b64encode(f"{USERNAME}:{PASSWORD}".encode()).decode()
        return {"Authorization": f"Basic {token}"}
    else:
        raise ValueError("No auth provided. Set ORACLE_FUSION_USERNAME/ORACLE_FUSION_PASSWORD or ORACLE_FUSION_OAUTH_TOKEN")

async def fusion_get(path_with_query: str):
    """
    Generic GET helper for Fusion REST APIs.
    Validates BASE_URL and returns a JSON-friendly error on failure.
    """
    if not BASE_URL:
        # explicit helpful error; do not call .rstrip on None
        raise ValueError("ORACLE_FUSION_BASE_URL is not set. Set this environment variable to the Fusion base URL, e.g. https://your-tenant.fa.us2.oraclecloud.com")

    url = BASE_URL.rstrip("/") + path_with_query
    headers = build_auth_headers()
    headers["Accept"] = "application/json"

    async with httpx.AsyncClient(timeout=30.0) as client:
        logger.debug("Calling Fusion GET %s", url)
        resp = await client.get(url, headers=headers)
        resp.raise_for_status()
        try:
            return resp.json()
        except Exception:
            return {"_raw": resp.text}

# Simple MCP tools

@mcp.tool()
async def ping_fusion() -> dict:
    """Check connectivity to Oracle Fusion"""
    try:
        if not BASE_URL:
            return {"ok": False, "error": "ORACLE_FUSION_BASE_URL not set"}
        # try a lightweight endpoint (may require permissions)
        test_path = "/fscmRestApi/resources/11.13.18.05/salesOrdersForOrderHub?limit=1"
        data = await fusion_get(test_path)
        return {"FusionBaseURL": BASE_URL, "ok": True, "sample": bool(data)}
    except Exception as e:
        logger.exception("ping_fusion failed")
        return {"FusionBaseURL": BASE_URL, "ok": False, "error": str(e)}

@mcp.tool()
async def list_sales_orders(limit: int = 5, q: str = None) -> dict:
    try:
        path = f"/fscmRestApi/resources/11.13.18.05/salesOrdersForOrderHub?limit={int(limit)}"
        if q:
            path += f"&q={quote_plus(q)}"
        data = await fusion_get(path)
        return {"items": data.get("items", []), "count": data.get("count", 0)}
    except Exception as e:
        logger.exception("list_sales_orders failed")
        return {"error": str(e)}

@mcp.tool()
async def list_draft_purchase_orders(limit: int = 5, q: str = None) -> dict:
    try:
        path = f"/fscmRestApi/resources/11.13.18.05/draftPurchaseOrders?limit={int(limit)}"
        if q:
            path += f"&q={quote_plus(q)}"
        data = await fusion_get(path)
        return {"items": data.get("items", []), "count": data.get("count", 0)}
    except Exception as e:
        logger.exception("list_draft_purchase_orders failed")
        return {"error": str(e)}

@mcp.tool()
async def get_sales_order_by_number(order_number: str) -> dict:
    try:
        path = f"/fscmRestApi/resources/11.13.18.05/salesOrdersForOrderHub?limit=1&q={quote_plus('OrderNumber=' + str(order_number))}"
        data = await fusion_get(path)
        items = data.get("items", [])
        return items[0] if items else {"error": f"No sales order {order_number}"}
    except Exception as e:
        logger.exception("get_sales_order_by_number failed")
        return {"error": str(e)}

@mcp.tool()
async def get_draft_po_by_id(po_id: str) -> dict:
    try:
        path = f"/fscmRestApi/resources/11.13.18.05/draftPurchaseOrders/{quote_plus(str(po_id))}"
        return await fusion_get(path)
    except Exception as e:
        logger.exception("get_draft_po_by_id failed")
        return {"error": str(e)}

# User/role helpers

@mcp.tool()
async def get_user_by_username(username: str) -> dict:
    """Get user account details by username including basic user information"""
    try:
        query = quote_plus(f"UserName='{username}'")

        # Try FSCM (hedUserAccounts)
        try:
            path = f"/fscmRestApi/resources/11.13.18.05/hedUserAccounts?q={query}"
            data = await fusion_get(path)
            items = data.get("items", [])
            if items:
                return items[0]
        except Exception as e:
            logger.debug(f"hedUserAccounts lookup failed: {e}")

        # Fallback: HCM userAccounts
        path2 = f"/hcmRestApi/resources/11.13.18.05/userAccounts?q={query}"
        data2 = await fusion_get(path2)
        items2 = data2.get("items", [])

        return items2[0] if items2 else {
            "error": f"No user found with username {username}"
        }

    except Exception as e:
        logger.exception("get_user_by_username failed")
        return {"error": str(e)}

@mcp.tool()
async def get_user_roles_by_guid(user_guid: str) -> dict:
    try:
        path = f"/hcmRestApi/resources/11.13.18.05/userAccounts/{quote_plus(user_guid)}/child/userAccountRoles"
        data = await fusion_get(path)
        return {"user_guid": user_guid, "roles": data.get("items", []), "total_roles": data.get("count", 0)}
    except Exception as e:
        logger.exception("get_user_roles_by_guid failed")
        return {"error": str(e)}

# Start MCP
if __name__ == "__main__":
    print("About to call mcp.run()", file=sys.stderr)
    try:
        mcp.run()
    except Exception as e:
        logger.exception("MCP server failed to start: %s", e)
        raise