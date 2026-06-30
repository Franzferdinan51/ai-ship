"""
AI-SHIP — Gitlawb Federated Bridge
======================================
Our MCP provider node that connects ai-ship to the gitlawb decentralized
git network. This script lets our model/dataset mirror announce itself to
any gitlawb peer, participate in the gossip mesh, and federate our index
across the network.

Architecture:
  ai-ship (our mirror)
       ↓  torrent + magnet
  gitlawb network (decentralized peers)
       ↓  MCP tools
  Any AI agent or human can discover and pull our models

Usage:
  python scripts/gitlawb_bridge.py                    # connect to local node
  python scripts/gitlawb_bridge.py --peer https://peer.gitlawb.com  # public network
  python scripts/gitlawb_bridge.py --mcp             # expose as MCP server

Requirements:
  - A running gitlawb node (gl node start)
    OR a public gitlawb peer URL
  - Python 3.9+
  - requests (for HTTP calls to the peer API)
"""

import argparse, json, os, sys, time, hashlib
from datetime import datetime
from config import GITLAWB_NODE_URL, GITLAWB_DID, TORRENTS_DIR, MODELS_DIR

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

# ─── MCP Tools ────────────────────────────────────────────────────────────────

MCP_TOOLS = {
    "discover_models": {
        "description": "Query the federated network for available models",
        "params": {"query": "str", "limit": "int"},
    },
    "announce_model": {
        "description": "Announce a mirrored model to the network",
        "params": {"repo_id": "str", "magnet_uri": "str", "size_bytes": "int"},
    },
    "check_network": {
        "description": "Check connectivity to gitlawb peers",
        "params": {},
    },
    "pull_model": {
        "description": "Get magnet URI and peer info for a specific model",
        "params": {"repo_id": "str"},
    },
}

# ─── Gitlawb API Client ────────────────────────────────────────────────────

class GitlawbClient:
    """Lightweight client for the gitlawb peer HTTP API."""

    def __init__(self, node_url=None, did=None):
        self.node_url = (node_url or GITLAWB_NODE_URL).rstrip("/")
        self.did = did or os.environ.get("GITLAWB_DID", "")
        self.session = requests.Session() if HAS_REQUESTS else None

    def _get(self, path, **kwargs):
        if not self.session:
            raise RuntimeError("requests not installed: pip install requests")
        r = self.session.get(f"{self.node_url}{path}", timeout=15, **kwargs)
        r.raise_for_status()
        return r.json()

    def _post(self, path, data=None, **kwargs):
        if not self.session:
            raise RuntimeError("requests not installed: pip install requests")
        r = self.session.post(f"{self.node_url}{path}", json=data, timeout=15, **kwargs)
        r.raise_for_status()
        return r.json()

    def ping(self):
        """Check peer connectivity."""
        try:
            return self._get("/health") or {"status": "ok"}
        except Exception as e:
            return {"error": str(e)}

    def repo_list_federated(self, query=""):
        """List repos known across the federated network."""
        params = {"q": query} if query else {}
        return self._get("/api/repos/federated", params=params)

    def repo_create(self, name, description="", is_public=True):
        """Create a repo on our node."""
        return self._post("/api/repos", {
            "name": name,
            "description": description,
            "public": is_public,
        })

    def did_resolve(self, did):
        """Resolve a DID to peer info."""
        return self._get(f"/api/did/{did}")

    def announce_model(self, repo_id, magnet_uri, size_bytes, metadata=None):
        """
        Announce a model/dataset as a federated repo.
        We create a repo entry on our node and broadcast via gossip.
        """
        # Create a repo for this model
        name = f"model-{repo_id.replace('/', '_')}"
        try:
            result = self.repo_create(name, description=f"AI-SHIP mirror of {repo_id}")
        except Exception as e:
            result = {"repo": name, "note": str(e)}

        # Write a manifest file describing the model
        manifest = {
            "type": "ai-ship model mirror",
            "repo_id": repo_id,
            "magnet_uri": magnet_uri,
            "size_bytes": size_bytes,
            "announced_at": datetime.utcnow().isoformat(),
            "metadata": metadata or {},
            "source": "huggingface",
        }

        # Write manifest to a file in our repos dir
        manifest_path = os.path.join(MODELS_DIR, f"{name}.manifest.json")
        os.makedirs(os.path.dirname(manifest_path), exist_ok=True)
        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)

        return {"repo": result, "manifest": manifest_path, "magnet": magnet_uri}

    def federated_search(self, query, limit=10):
        """
        Search across all federated peers for models.
        Aggregates results from connected peers.
        """
        try:
            results = self.repo_list_federated(query=query)
            return results.get("repos", [])[:limit]
        except Exception as e:
            return [{"error": str(e)}]

# ─── Bridge Engine ─────────────────────────────────────────────────────────

class AIShipBridge:
    """
    The main bridge: reads our local index and announces it to gitlawb peers.
    Also listens for gossip about models from other peers.
    """

    def __init__(self, peer_url=None, did=None):
        self.client = GitlawbClient(node_url=peer_url, did=did)
        self.announced = set()

    def check(self):
        """Health check — are we connected?"""
        return self.client.ping()

    def discover(self, query="", limit=10):
        """
        Discover models across the federated network.
        Returns list of model entries from all connected peers.
        """
        return self.client.federated_search(query, limit=limit)

    def announce_local_index(self):
        """
        Scan our local db/index and announce everything to the network.
        Only announces new items (tracks announced set).
        """
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
        from db import get_all, stats

        all_items = get_all()  # gets all models and datasets
        results = []
        for item in all_items:
            slug = item["slug"]
            if slug in self.announced:
                continue
            try:
                result = self.client.announce_model(
                    repo_id=item["repo_id"],
                    magnet_uri=item.get("magnet", ""),
                    size_bytes=item.get("size_bytes", 0),
                    metadata={
                        "item_type": item["item_type"],
                        "title": item.get("title", ""),
                    },
                )
                self.announced.add(slug)
                results.append(result)
                print(f"  Announced: {item['repo_id']}")
            except Exception as e:
                print(f"  Failed: {item['repo_id']} — {e}")
        return results

    def seed_loop(self, interval=300):
        """
        Run the announce loop indefinitely.
        Announces new items every `interval` seconds.
        """
        print(f"[AI-SHIP Bridge] Starting seed loop (announce every {interval}s)")
        print(f"[AI-SHIP Bridge] Peer: {self.client.node_url}")
        while True:
            try:
                results = self.announce_local_index()
                if not results:
                    print(f"[{datetime.now().isoformat()}] No new items to announce")
                else:
                    print(f"[{datetime.now().isoformat()}] Announced {len(results)} items")
            except Exception as e:
                print(f"[AI-SHIP Bridge] Error: {e}")
            time.sleep(interval)

# ─── MCP Server ────────────────────────────────────────────────────────────

def run_mcp_server(bridge):
    """
    Expose our bridge as an MCP server so any MCP-compatible AI agent
    (Claude, GPT, Grok) can query our model index via gitlawb peers.

    This is the federated layer: an AI agent anywhere in the world
    can ask our mirror "what models are available" and get an answer
    without any central server.
    """
    from mcp.server import Server
    from mcp.types import Tool, CallToolRequest

    server = Server("ai-ship")

    @server.list_tools()
    async def list_tools():
        return [
            Tool(
                name=name,
                description=spec["description"],
                inputSchema={"type": "object", "properties": {"query": {"type": "string"}}}
            )
            for name, spec in MCP_TOOLS.items()
        ]

    @server.call_tool()
    async def call_tool(name, arguments):
        if name == "discover_models":
            results = bridge.discover(
                query=arguments.get("query", ""),
                limit=arguments.get("limit", 10),
            )
            return [{"text": json.dumps(results, indent=2)}]
        elif name == "announce_model":
            # handled internally — not exposed to outside callers
            return [{"text": "Use ai-ship's internal index instead"}]
        elif name == "check_network":
            return [{"text": json.dumps(bridge.check())}]
        elif name == "pull_model":
            results = bridge.discover(arguments.get("repo_id", ""))
            return [{"text": json.dumps(results[:1], indent=2)}]
        return [{"text": "Unknown tool"}]

    return server

# ─── CLI ─────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="AI-SHIP Gitlawb Bridge")
    parser.add_argument("--peer", default=os.environ.get("GITLAWB_PEER_URL", ""),
                        help="Gitlawb peer URL (default: localhost:7545)")
    parser.add_argument("--did", default="",
                        help="Our DID (from: gl identity create)")
    parser.add_argument("--mcp", action="store_true",
                        help="Run as MCP server")
    parser.add_argument("--seed", action="store_true",
                        help="Run the seed/announce loop")
    parser.add_argument("--interval", type=int, default=300,
                        help="Seconds between announces (default: 300)")
    parser.add_argument("--check", action="store_true",
                        help="Check network connectivity and exit")
    args = parser.parse_args()

    peer_url = args.peer or "http://localhost:7545"
    bridge = AIShipBridge(peer_url=peer_url, did=args.did)

    if args.check:
        result = bridge.check()
        print(json.dumps(result, indent=2))
        return

    if args.mcp:
        server = run_mcp_server(bridge)
        # Run with stdin/stdout transport (MCP stdio mode)
        from mcp.server.stdio import serve
        import asyncio
        asyncio.run(serve(server))

    elif args.seed:
        bridge.seed_loop(interval=args.interval)

    else:
        # Default: announce all local items once and print results
        print(f"[AI-SHIP Bridge] Connecting to {peer_url}")
        health = bridge.check()
        print(f"[Health] {json.dumps(health)}")
        print(f"[AI-SHIP Bridge] Announcing local index...")
        results = bridge.announce_local_index()
        print(f"[Done] Announced {len(results)} items")

if __name__ == "__main__":
    main()
