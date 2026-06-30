# Accreditation — AI-SHIP

This project exists because of the open-source ecosystem it builds on.

---

## Sources and Inspiration

### Gitlawb (`gitlawb/node`, `gitlawb/openclaude`)
**License:** MIT / Apache-2.0
**URL:** https://github.com/Gitlawb

Gitlawb's architecture is the inspiration for AI-SHIP's decentralized philosophy:
- **Ed25519 DID identity** — cryptographic identity without accounts or passwords
- **libp2p peer discovery** — nodes finding each other without central servers
- **Git objects on IPFS** — content-addressed storage so repos don't disappear
- **MCP server per node** — every node exposes 25 tools for AI agents to interact with

The key insight from Gitlawb: once code or data is pushed to a decentralized network,
it cannot disappear because one server went down. AI-SHIP applies this same principle
to AI model weights and datasets.

### HuggingFace (`huggingface/transformers`, `huggingface Hub`)
**License:** Apache-2.0 (most models), varies by model
**URL:** https://huggingface.co

The HuggingFace Hub is the de facto source for open AI models and datasets.
AI-SHIP mirrors HuggingFace content via torrent to ensure availability if HF is
ever blocked, banned, or taken offline.

### premAI (`premAI-io/from-hf-to-torrent`)
**License:** MIT
**URL:** https://github.com/premAI-io/from-hf-to-torrent

premAI's torrent infrastructure showed that large model files can be distributed
via BitTorrent effectively. Their work on seeding popular open models proved the
model is viable for decentralized distribution.

### Academic Torrents (`academictorrents`)
**License:** MIT
**URL:** https://academictorrents.com

Academic Torrents demonstrated that scientific datasets can survive via
BitTorrent when institutional funding runs out. Their 298TB+ archive proved
decentralized research data storage at scale.

### Internet Archive / Wayback Machine
**License:** CC BY 4.0
**URL:** https://archive.org

The Internet Archive's work on preserving public data — including AI chatbot
outputs and government records — demonstrates why someone has to actively preserve
knowledge infrastructure before it disappears.

---

## Technical Foundations

| Component | Source | Purpose |
|---|---|---|
| BitTorrent encoding | Public spec (BEP 3, 5, 12) | Model/dataset distribution |
| Content-addressing (CID/IPFS) | Protocol Labs | Immutable file addresses |
| Ed25519 / did:key | Gitlawb / W3C DID spec | Identity without accounts |
| RFC 9421 HTTP Signatures | IETF | Authenticated writes |
| SQLite | Public domain | Local index storage |
| Flask | BSD | Web UI |

---

## For Users

If you download a model via AI-SHIP, credit the original model author on
HuggingFace. Their license applies. AI-SHIP is a distribution mirror,
not a replacement for the original license.

---

## For Contributors

If you fork AI-SHIP to build something new:
1. Keep this accreditation file and credit the sources above
2. Preserve the Apache-2.0 / MIT licensing of the tools themselves
3. Attribute HuggingFace model authors per their model licenses
4. If you add gitlawb integration, respect their MIT/Apache-2.0 license

The goal is open access to AI — not claiming someone else's work as your own.
