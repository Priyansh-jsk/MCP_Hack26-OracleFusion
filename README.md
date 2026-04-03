# Oracle Fusion MCP Server

I have developed an MCP Server that connects with Oracle Fusion to simplify enterprise data access with Oracle Fusion Cloud APIs to fetch:

- Purchase Orders
- Sales Orders
- User details
- User roles & permissions

# What This Project Does

This MCP server enables AI tools (like Claude Desktop) to:

Query Oracle Fusion data in real-time
Retrieve latest sales & purchase orders
Fetch user roles and access information
Perform role-based insights

**Tech Stack**

- Python 3.10+
- MCP (FastMCP)
- httpx (async API calls)
- Oracle Fusion REST APIs
  
**Project Structure**

MCP_fusion/
│── app.py              # Main MCP server
│── requirements.txt   # Dependencies
│── .env

**Setup Update your MCP config JSON:**

{
  "mcpServers": {
    "mcpServer_fusion": {
      "command": "uv",
      "args": [
        "--directory",
        "C:/path/to/MCP_fusion",
        "run",
        "app.py"
      ]
    }
  }
}

**Example Prompts (Try in Claude)**

“Show me latest 5 sales orders”
“List draft purchase orders”
“Get user details for username X”
“What roles are assigned to user X?”

**Available MCP Tools**

Tool	Description

- ping_fusion	Check Fusion connection
- list_sales_orders	Get sales orders
- list_draft_purchase_orders	Get draft POs
- get_sales_order_by_number	Fetch specific SO
- get_draft_po_by_id	Fetch specific PO
- get_user_by_username	Fetch user info
- get_user_roles_by_guid	Get user roles

**Author**

Built by [Priyansh Neema]

If you like this project Give it a ⭐ on GitHub!


