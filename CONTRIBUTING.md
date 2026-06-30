# Contributing to AI-SHIP

Thank you for building with us. Here's how to contribute.

---

## What We're Building

AI-SHIP is a decentralized mirror for AI models and datasets — a fallback
infrastructure so that if HuggingFace ever gets blocked, banned, or goes down,
the open AI commons don't disappear with it.

The three layers:
1. **Download** — Mirror models from HuggingFace
2. **Distribute** — Create torrents, seed them via BitTorrent
3. **Federate** — Announce models across the gitlawb decentralized git network

---

## Ways to Contribute

### 1. Seed Models
Download a model, create its torrent, seed it. Even one seeder is enough.

```bash
# Install
pip install -r requirements.txt

# Download a model
python app.py
# → Search HuggingFace → Download

# Seed it
qbittorrent data/torrents/*.torrent
```

### 2. Run a Gitlawb Node
Join the federated network. Your node announces our models to peers.

```bash
# Install gitlawb CLI
npm install -g @gitlawb/gl

# Create identity
gl identity create

# Start your node
gl node start

# In another terminal: announce our models
python scripts/gitlawb_bridge.py --seed
```

### 3. Improve the Code

| Area | What needs work |
|---|---|
| `torrent.py` | Pure Python fallback when torf isn't available |
| `app.py` | Add user auth, model page ratings, comments |
| `downloader.py` | Dataset downloading, resume support |
| `scripts/seed_daemon.py` | Automated seeding with qBittorrent CLI |
| `scripts/search_models.py` | Better HF metadata scraping |

### 4. Write Docs
- Architecture diagrams
- How to set up on a VPS
- How to seed on a Raspberry Pi
- How to integrate with other tools

---

## Development Setup

```bash
git clone https://github.com/Franzferdinan51/ai-ship.git
cd ai-ship
pip install -r requirements.txt

# Run tests (if any)
python -m pytest

# Start dev server
python app.py
```

---

## Pull Request Guidelines

1. **Scope** — One PR per thing. Fix a bug, add one feature, write one doc.
2. **Test** — If you add a feature, show it working.
3. **Commit** — Use clear messages: `fix: bdecode dict key parsing` not `update stuff`
4. **Attribution** — If you use someone's code or idea, credit it in the commit and ACCREDITATION.md

---

## Code Standards

- Pure Python 3.9+ — no Python 2
- Stdlib where possible — don't add deps unless necessary
- Windows-compatible paths — use `pathlib` or `os.path`
- No secrets in code — use env vars or `.env` file
- Dark-themed UI — keep the #0d1117 background

---

## Issues to Start With

Look at the GitHub Issues for labeled `good first issue` or `help wanted`.

---

## License

AGPLv3 — same as the project. If you fork it for a specific deployment
and don't modify the core logic, you can run it under your own license.
