# AI-SHIP

> Decentralized mirror for AI models and datasets — built on Gitlawb.

## What

AI-SHIP mirrors HuggingFace models and datasets and distributes them through the
Gitlawb decentralized git network. If HuggingFace ever gets blocked, banned, or
goes down, the open AI commons don't disappear.

**Scope:** AI models, datasets, weights, and related artifacts.

**Not in scope:** Pirated software, non-AI content, anything illegal.

## Why

The AI ecosystem is dangerously centralized. HuggingFace hosts the vast majority of
open-source models on a single cloud. Gitlawb gives us a decentralized federated
network — Ed25519 DID identity, libp2p peer discovery, IPFS pinning — so models
mirrored here survive without any central server.

## Architecture

```
HuggingFace
    ↓ download
ai-ship mirror
    ↓ announce via MCP bridge
Gitlawb network ← Ed25519 DID, libp2p, IPFS, Gossipsub
    ↓
Federated peers — any node can pull and re-seed
```

Gitlawb's infrastructure handles:
- **Identity** — Ed25519 DID keypairs, no accounts
- **Discovery** — libp2p DHT peer discovery
- **Storage** — IPFS pinning for git objects
- **Federation** — gossipsub broadcasts across all peers
- **MCP** — 25 tools per node, AI agents can query directly

## Setup

```bash
git clone https://github.com/Franzferdinan51/ai-ship.git
cd ai-ship
pip install -r requirements.txt
python app.py
# → http://localhost:5000
```

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
```

## API

| Endpoint | Method | Description |
|---|---|---|
| `/api/stats` | GET | Total models, datasets, size |
| `/api/search?q=llama` | GET | Search HuggingFace |
| `/api/download` | POST | Download + register |
| `/api/add` | POST | Register without downloading |

## License

AGPL v3 — see LICENSE
