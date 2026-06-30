# AI-SHIP

> Decentralized mirror for AI models and datasets — built on Gitlawb.
> No accounts. No gatekeepers. Models survive without any central server.

---

## The Problem

HuggingFace hosts the vast majority of open AI models on a single cloud. If it
gets blocked, banned, or has a bad day, a massive chunk of open AI disappears
with it.

AI-SHIP mirrors HuggingFace models and distributes them through the **Gitlawb
decentralized git network** — Ed25519 DID identity, libp2p peer discovery,
IPFS pinning, and federated MCP tools. If HuggingFace goes down, the open AI
commons are still available from any gitlawb peer.

## The Stack

```
HuggingFace
    ↓ download
ai-ship mirror
    ↓ announce via MCP
Gitlawb network
    ├─ libp2p peer discovery    ← nodes find each other
    ├─ IPFS content pinning     ← content-addressed, immutable
    ├─ Gossipsub broadcasts     ← model availability spreads peer-to-peer
    ├─ Ed25519 DID identity     ← no accounts, cryptographic
    └─ MCP server (25 tools)   ← any AI agent can query the network
    ↓
Any AI agent or node operator pulls models — no central server needed
```

## Quick Start

```bash
git clone https://github.com/Franzferdinan51/ai-ship.git
cd ai-ship
pip install -r requirements.txt
python app.py
# → http://localhost:5000
```

## Three Interfaces

### Web UI
`python app.py` — browse models, search HuggingFace, download and register.

### REST API
`python scripts/api.py` — 14 endpoints for scripts and integrations.

```bash
# Mirror a model
curl -X POST http://localhost:5000/api/register \
  -H "Content-Type: application/json" \
  -d '{"type": "model", "repo_id": "openai/whisper-tiny"}'

# Search HuggingFace
curl "http://localhost:5000/api/hf/search/models?q=llama&limit=5"

# Check stats
curl http://localhost:5000/api/stats
```

### MCP (for AI agents)
`python scripts/mcp_server.py` — exposes 8 tools to any MCP-compatible AI:
Claude, GPT, Codex, Grok, Cursor, Windsurf, and any other MCP client.

Configure in your MCP client:
```json
{
  "mcpServers": {
    "ai-ship": {
      "command": "python",
      "args": ["C:/Users/franz/Desktop/ai-ship/scripts/mcp_server.py"]
    }
  }
}
```

Then ask your AI: *"What models are available on my AI-SHIP mirror?"*

### CLI
```bash
python scripts/cli.py search "stable diffusion" --limit 5
python scripts/cli.py models --search llama
python scripts/cli.py download openai/whisper-tiny --type model
python scripts/cli.py stats
python scripts/cli.py federation health
python scripts/cli.py federation announce
```

## MCP Tools

| Tool | Description |
|---|---|
| `hf_search_models` | Search HuggingFace for models |
| `hf_search_datasets` | Search HuggingFace for datasets |
| `ship_list_models` | List mirrored models |
| `ship_list_datasets` | List mirrored datasets |
| `ship_get_model` | Get details for a specific model |
| `ship_stats` | Mirror statistics |
| `ship_download` | Download + register a model |
| `ship_federated_search` | Search federated peers for models |

## REST Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Health check for monitoring |
| GET | `/api/stats` | Mirror statistics |
| GET | `/api/models` | List mirrored models |
| GET | `/api/datasets` | List mirrored datasets |
| GET | `/api/items/<slug>` | Get item details |
| GET | `/api/hf/search/models` | Search HuggingFace models |
| GET | `/api/hf/search/datasets` | Search HuggingFace datasets |
| POST | `/api/download` | Download from HF and register |
| POST | `/api/register` | Register without downloading |
| GET | `/api/federation/search` | Search gitlawb peers |
| GET | `/api/federation/health` | Check peer connectivity |
| POST | `/api/federation/announce` | Broadcast local index to peers |

## Federate with Gitlawb

```bash
# Install gitlawb CLI
npm install -g @gitlawb/gl

# Create your DID identity
gl identity create

# Start your node
gl node start

# Announce our model index to the network
python scripts/gitlawb_bridge.py --seed

# Check connectivity
python scripts/gitlawb_bridge.py --check
```

Your node now participates in the federated model network. Other peers can discover
your mirrored models, and your AI agents can discover theirs.

## Docker

```bash
# Build and run
docker build . -t ai-ship
docker run -p 5000:5000 -v ./models:/data/models ai-ship

# Or with docker-compose
docker compose up
```

## Project Structure

```
ai-ship/
├── app.py                      # Flask web UI
├── db.py                       # SQLite mirror index
├── downloader.py               # HuggingFace Hub downloader
├── config.py                   # Configuration
│
├── scripts/
│   ├── mcp_server.py           # MCP server (8 tools)
│   ├── api.py                  # REST API (14 endpoints)
│   ├── cli.py                  # CLI
│   └── gitlawb_bridge.py       # Gitlawb federated bridge
│
├── tests/
│   └── __init__.py             # pytest test suite
│
├── .github/workflows/
│   └── ci.yml                  # CI: pytest + API smoke + lint
│
├── Dockerfile
├── docker-compose.yml
├── API.md                      # Full API reference
├── INTEGRATION.md              # Gitlawb integration docs
├── CONTRIBUTING.md
├── ACCREDITATION.md
└── README.md (this file)
```

## Why It Exists

1. **Resilience** — if HuggingFace gets blocked or goes down, models are still
   available from any gitlawb peer
2. **Censorship resistance** — no central server to pressure or takedown
3. **AI agent access** — any AI agent on the network can query the mirror via MCP
4. **No accounts** — Ed25519 DID identity, cryptographic, no gatekeepers

## Scope

**In scope:** AI models, datasets, weights, and artifacts from HuggingFace.

**Not in scope:** Pirated software, non-AI content, anything illegal.

## License

AGPL v3 — see LICENSE
