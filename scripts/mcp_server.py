"""
AI-SHIP MCP Server
===================
Model Context Protocol server that exposes our model index to any
MCP-compatible AI agent. Works with Claude (via mcp:/// in claude_desktop_config.json),
OpenAI Codex, Cursor, Windsurf, and any other MCP client.

Run standalone:
  python scripts/mcp_server.py

Or configure in your MCP client (e.g. Claude Desktop):
  Add to ~/.claudeaude_desktop_config.json:
  {
    "mcpServers": {
      "ai-ship": {
        "command": "python",
        "args": ["C:/Users/franz/Desktop/ai-ship/scripts/mcp_server.py"]
      }
    }
  }
"""
import os, sys, json, asyncio
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Add parent dir to path so we can import app modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from db import get_all, get_by_slug, stats, count_items
from downloader import list_hf_models, list_hf_datasets, download_model, download_dataset
from config import WEB_HOST, WEB_PORT

SERVER_NAME = "ai-ship"

# ─── Tool Definitions ────────────────────────────────────────────────────────

TOOLS = [
    Tool(
        name="hf_search_models",
        description="Search HuggingFace Hub for models by keyword. Returns top results with download counts, tags, and author.",
        inputSchema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search keyword (e.g. 'llama', 'stable diffusion', 'whisper')"},
                "limit": {"type": "integer", "description": "Max results (default 10, max 50)", "default": 10},
            },
            "required": ["query"],
        },
    ),
    Tool(
        name="hf_search_datasets",
        description="Search HuggingFace Hub for datasets by keyword.",
        inputSchema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search keyword"},
                "limit": {"type": "integer", "description": "Max results (default 10, max 50)", "default": 10},
            },
            "required": ["query"],
        },
    ),
    Tool(
        name="ship_list_models",
        description="List all models registered in the local AI-SHIP mirror index.",
        inputSchema={
            "type": "object",
            "properties": {
                "search": {"type": "string", "description": "Filter by name substring"},
                "limit": {"type": "integer", "description": "Max results (default 20)", "default": 20},
                "offset": {"type": "integer", "description": "Pagination offset", "default": 0},
            },
        },
    ),
    Tool(
        name="ship_list_datasets",
        description="List all datasets registered in the local AI-SHIP mirror index.",
        inputSchema={
            "type": "object",
            "properties": {
                "search": {"type": "string", "description": "Filter by name substring"},
                "limit": {"type": "integer", "description": "Max results (default 20)", "default": 20},
                "offset": {"type": "integer", "description": "Pagination offset", "default": 0},
            },
        },
    ),
    Tool(
        name="ship_get_model",
        description="Get full details for a specific model or dataset by its slug (repo_id with slashes replaced by underscores).",
        inputSchema={
            "type": "object",
            "properties": {
                "slug": {"type": "string", "description": "The item slug, e.g. 'meta-llama_Llama-3-8B'"},
            },
            "required": ["slug"],
        },
    ),
    Tool(
        name="ship_stats",
        description="Get AI-SHIP mirror statistics: total models, datasets, downloaded count, total size in bytes.",
        inputSchema={"type": "object", "properties": {}},
    ),
    Tool(
        name="ship_download",
        description="Download a model or dataset from HuggingFace and register it in the AI-SHIP index.",
        inputSchema={
            "type": "object",
            "properties": {
                "repo_id": {"type": "string", "description": "HuggingFace repo ID, e.g. 'openai/whisper-tiny'"},
                "item_type": {"type": "string", "description": "'model' or 'dataset'", "enum": ["model", "dataset"]},
            },
            "required": ["repo_id", "item_type"],
        },
    ),
    Tool(
        name="ship_federated_search",
        description="Search the federated network (via gitlawb peers) for models available from other mirrors. Returns peer info and model metadata.",
        inputSchema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search keyword"},
                "limit": {"type": "integer", "description": "Max results", "default": 10},
            },
        },
    ),
]

# ─── Server ─────────────────────────────────────────────────────────────────

server = Server(SERVER_NAME)

@server.list_tools()
async def list_tools():
    return TOOLS

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    try:
        if name == "hf_search_models":
            results = list_hf_models(
                query=arguments.get("query", ""),
                limit=min(arguments.get("limit", 10), 50),
            )
            return [TextContent(type="text", text=json.dumps(results, indent=2))]

        elif name == "hf_search_datasets":
            results = list_hf_datasets(
                query=arguments.get("query", ""),
                limit=min(arguments.get("limit", 10), 50),
            )
            return [TextContent(type="text", text=json.dumps(results, indent=2))]

        elif name == "ship_list_models":
            items = get_all(
                item_type="model",
                search=arguments.get("search", ""),
                limit=min(arguments.get("limit", 20), 100),
                offset=arguments.get("offset", 0),
            )
            return [TextContent(type="text", text=json.dumps(items, indent=2))]

        elif name == "ship_list_datasets":
            items = get_all(
                item_type="dataset",
                search=arguments.get("search", ""),
                limit=min(arguments.get("limit", 20), 100),
                offset=arguments.get("offset", 0),
            )
            return [TextContent(type="text", text=json.dumps(items, indent=2))]

        elif name == "ship_get_model":
            item = get_by_slug(arguments["slug"])
            if not item:
                return [TextContent(type="text", text=f"Item not found: {arguments['slug']}")]
            return [TextContent(type="text", text=json.dumps(item, indent=2))]

        elif name == "ship_stats":
            s = stats()
            s["total_size_gb"] = round(s["total_size_bytes"] / 1e9, 2) if s["total_size_bytes"] else 0
            return [TextContent(type="text", text=json.dumps(s, indent=2))]

        elif name == "ship_download":
            repo_id = arguments["repo_id"]
            item_type = arguments["item_type"]
            if item_type == "model":
                path, result = download_model(repo_id)
            else:
                path, result = download_dataset(repo_id)
            if path is None:
                return [TextContent(type="text", text=f"Download failed: {result}")]
            return [TextContent(type="text", text=json.dumps({"ok": True, "path": path, "size": result}, indent=2))]

        elif name == "ship_federated_search":
            # Try to reach gitlawb peers; gracefully return empty if not connected
            try:
                sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
                from gitlawb_bridge import AIShipBridge
                bridge = AIShipBridge()
                results = bridge.discover(query=arguments.get("query", ""),
                                         limit=arguments.get("limit", 10))
                return [TextContent(type="text", text=json.dumps(results, indent=2))]
            except Exception as e:
                return [TextContent(type="text", text=json.dumps({"error": str(e), "note": "Gitlawb node not connected — run: gl node start"}))]

        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]

    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]

# ─── Main ───────────────────────────────────────────────────────────────────

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )

if __name__ == "__main__":
    asyncio.run(main())
