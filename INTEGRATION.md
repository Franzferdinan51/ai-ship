# AI-SHIP + Gitlawb Integration

> How AI-SHIP uses Gitlawb as its decentralized infrastructure layer.

---

## Why Gitlawb

The open AI ecosystem is dangerously centralized. HuggingFace hosts the vast
majority of open models on a single cloud. If it goes down or gets blocked,
a massive chunk of open AI disappears.

BitTorrent solves the distribution problem. But torrent files still need
a tracker — and trackers can be blocked or pressured.

Gitlawb solves the discovery and identity problem:
- **Ed25519 DID identity** — no accounts, cryptographic
- **libp2p peer discovery** — nodes find each other without DNS or central servers
- **Git objects on IPFS** — content-addressed, immutable, persistent
- **MCP server per node** — every node exposes 25 tools for AI agents

---

## The Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                     HuggingFace Hub                         │
│          (models, datasets, weights — centralized)           │
└──────────────────────────┬───────────────────────────────────┘
                           │ download
                           ▼
┌──────────────────────────────────────────────────────────────┐
│                       AI-SHIP                                │
│  downloader.py ──► torrent.py ──► db.py + web UI           │
│                                                              │
│  Creates .torrent files for every model we mirror.         │
│  Generates magnet URIs. Seeds via BitTorrent.                │
└───────────────┬──────────────────────────────────┬──────────┘
                │ announce via MCP                    │ federate
                ▼                                     ▼
┌──────────────────────────────────────────────────────────────┐
│                   Gitlawb Network                             │
│                                                              │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐                │
│  │  Node A  │◄─►│  Node B  │◄─►│  Node C  │  ...         │
│  │ (us)    │   │          │   │          │                │
│  └────┬────┘   └──────────┘   └──────────┘                │
│       │                                                    │
│       │ MCP tools (25)                                     │
│       │ • discover_models()                                │
│       │ • announce_model(repo_id, magnet)                  │
│       │ • pull_model(repo_id)                              │
│       │ • check_network()                                  │
│       ▼                                                    │
│  Any AI agent (Claude, GPT, Grok) can query our mirror     │
│  without any central server — just peer-to-peer DIDs       │
└──────────────────────────────────────────────────────────────┘
```

---

## What Each Layer Does

| Layer | Responsibility | Our Code |
|---|---|---|
| **HuggingFace** | Model source, licensing, identity | — |
| **AI-SHIP** | Download, torrent creation, local index | `downloader.py`, `torrent.py`, `db.py` |
| **BitTorrent** | Distribution without central servers | `qbittorrent`, `transmission-cli` |
| **Gitlawb** | Discovery, identity, federation, MCP | `scripts/gitlawb_bridge.py` |

---

## Gitlawb Components We Use

### `gitlawb-node`
The Rust daemon. Runs on our server or a VPS.
```
docker compose up -f gitlawb/node/docker-compose.yml
```

### `gl` CLI
Creates our DID identity and manages our node.
```
gl identity create
gl node start
```

### `git-remote-gitlawb`
Git remote helper. Lets normal `git push` work with our node.
```
git remote add gitlawb gitlawb://did:key:z6Mk...
git push gitlawb main
```

### MCP Server (25 tools per node)
Every gitlawb node exposes an MCP server. Our bridge uses:
- `repo_list_federated` — discover models across all peers
- `repo_create` — announce a new model
- `did_resolve` — find a peer's network address from their DID
- `mcp_subscribe` — listen for model availability broadcasts

---

## Our Bridge (`scripts/gitlawb_bridge.py`)

Our bridge runs as a **federated MCP provider**:

1. **Discovers** — Queries all connected gitlawb peers for known models
2. **Announces** — Broadcasts our mirrored models to the network
3. **Responds** — AI agents anywhere can ask "what models are available"
4. **Federates** — Model index is distributed — no single point of failure

### Running the bridge

```bash
# Connect to your local gitlawb node
python scripts/gitlawb_bridge.py --check
python scripts/gitlawb_bridge.py --seed

# Or as an MCP server for an AI agent
python scripts/gitlawb_bridge.py --mcp
```

### MCP Tools We Expose

| Tool | What it does |
|---|---|
| `discover_models(query)` | Search federated network for models |
| `announce_model(repo_id, magnet, size)` | Broadcast a model to all peers |
| `check_network()` | Are we connected to any peers? |
| `pull_model(repo_id)` | Get magnet URI for a specific model |

---

## Data Flow for a New Model

```
1. User searches HuggingFace via app.py
2. User clicks Download
3. downloader.py fetches model weights from HF
4. torrent.py creates .torrent for the model directory
5. db.py records: repo_id, magnet URI, size, created_at
6. gitlawb_bridge.py reads db, creates a federated repo entry
7. Gitlawb gossips the new repo to all connected peers
8. Any AI agent on the network can now discover and pull the model
```

---

## What We Add to Gitlawb

Gitlawb is built for **git repositories**. We extend it for **model weights**:

| Gitlawb concept | Our equivalent |
|---|---|
| Git repository | Model/dataset mirror |
| Git commit | Model version update |
| Branch | Model variant (GGUF, AWQ, pruned) |
| Fork | Full mirror copy on another node |
| Clone | Torrent download of model weights |
| Push | Announce model to peers |
| Pull | Query peers for model, download via magnet |

---

## Persistence Without Gitlawb

Gitlawb is the **federation layer**. The **persistence layer** is BitTorrent.

Even if no gitlawb peer is online, the `.torrent` files work standalone:
- Anyone with the magnet URI can download the model
- Seeders keep the model alive
- No server required — just the magnet and peers

Gitlawb adds: *"How do I find peers who have this model?"*
BitTorrent answers: *"Once I find them, how do I download it?"*

Together they make a fully decentralized model distribution system.

---

## Accreditation

We build on Gitlawb's open-source infrastructure. See ACCREDITATION.md
for the full list of sources and inspirations.
