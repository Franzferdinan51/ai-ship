# AI-SHIP Installation Guide

## Prerequisites

- **Python 3.10+** — [python.org/downloads](https://python.org/downloads)
- **Git** — for cloning
- **Internet connection** — to download from HuggingFace

Optional:
- **Docker** — for containerized setup
- **Node.js** — for gitlawb CLI (`npm install -g @gitlawb/gl`)

## 1. Clone

```bash
git clone https://github.com/Franzferdinan51/ai-ship.git
cd ai-ship
```

## 2. Install Dependencies

```bash
pip install -r requirements.txt
```

## 3. Run

```bash
# Web UI + full REST API
python app.py
# → http://localhost:5000

# REST API only
python scripts/api.py

# CLI
python scripts/cli.py stats
python scripts/cli.py search "stable diffusion"
```

## 4. Docker

```bash
docker build . -t ai-ship
docker run -p 5000:5000 -v $(pwd)/models:/data/models ai-ship

# docker-compose
docker compose up
```

## 5. Federate with Gitlawb (Optional)

```bash
npm install -g @gitlawb/gl
gl identity create
gl node start

# Announce models to the network
python scripts/gitlawb_bridge.py --seed
```

## Troubleshooting

### Module not found
```bash
pip install -r requirements.txt
```

### Port 5000 already in use
Change `WEB_PORT` in `config.py` or:
```bash
WEB_PORT=5001 python app.py
```

### HuggingFace rate limiting
Get a free token at [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens),
then set `HF_TOKEN=*** in your environment.

## Updating

```bash
cd ai-ship
git pull origin main
pip install -r requirements.txt --upgrade
```
