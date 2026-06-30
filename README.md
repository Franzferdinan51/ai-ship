# AI-SHIP

> Decentralized mirror for AI models, datasets, and related materials.
> Built for open access. No single server. No single point of failure.

## What

AI-SHIP is a self-hosted mirror for the AI ecosystem. It downloads models and datasets
from HuggingFace, creates torrent files, and lets you seed them so that if HuggingFace
ever goes down or gets banned, the content is still available via BitTorrent.

**Scope:**
- AI models (LLMs, vision models, audio models, etc.)
- Training and evaluation datasets
- Model weights and checkpoints
- Related AI artifacts (tokenizers, configs, etc.)

**Not in scope:** Pirated software, non-AI content, anything illegal.

## Why

The AI ecosystem is dangerously centralized. HuggingFace hosts the vast majority of
open-source models and datasets on a single cloud provider. If HuggingFace gets banned,
blocked, or shut down, a massive chunk of the open AI commons disappears overnight.

BitTorrent is nearly impossible to take down. Once a model is torrented and seeded by
enough people, it lives forever — no single server to target, no domain to seize.

## Architecture

```
ai-ship/
├── app.py           # Flask web UI
├── db.py            # SQLite index of all models/datasets
├── downloader.py    # HuggingFace Hub downloader
├── torrent.py       # Pure-Python torrent creator
├── config.py        # Paths, settings
├── templates/       # Web UI HTML
└── data/
    ├── models/      # Downloaded models
    ├── datasets/    # Downloaded datasets
    └── torrents/    # Generated .torrent files
```

## Setup

```bash
# Clone
git clone https://github.com/YOUR_USERNAME/ai-ship.git
cd ai-ship

# Install dependencies
pip install -r requirements.txt

# Run
python app.py
```

Then open http://127.0.0.1:5000

## Usage

### Browse and search
Use the web UI to search HuggingFace and see what's available.

### Download and seed
Click any model or dataset to download it and create a torrent.
The torrent is saved to `data/torrents/` and you can seed it.

### Register-only (no download)
Use the API to register a HuggingFace model in the index without downloading:
```
POST /api/add
{"type": "model", "repo_id": "meta-llama/Llama-3-8B"}
```

### Seed an existing model
Download a model manually, put it in `data/models/`, then run:
```python
from torrent import create_and_save
create_and_save("data/models/my_model/", "my_model")
```

## API

| Endpoint | Method | Description |
|---|---|---|
| `/api/stats` | GET | Total models, datasets, size |
| `/api/search?q=llama` | GET | Search HuggingFace |
| `/api/download` | POST | Download + create torrent |
| `/api/add` | POST | Register without downloading |
| `/torrents/<slug>` | GET | Download .torrent file |

## torrents/ directory

Place any .torrent files in `data/torrents/` to make them available via the web UI.
Others can download the .torrent and seed the same content.

## License

AGPL v3 — see LICENSE
