"""
AI-SHIP — Config
Decentralized mirror for AI models, datasets, and related materials.
"""
import os

# Base paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, "models")
DATASETS_DIR = os.path.join(BASE_DIR, "datasets")
TORRENTS_DIR = os.path.join(BASE_DIR, "torrents")
DB_PATH = os.path.join(BASE_DIR, "db", "index.db")

# Create dirs if missing
for d in [MODELS_DIR, DATASETS_DIR, TORRENTS_DIR]:
    os.makedirs(d, exist_ok=True)

# Web UI
WEB_HOST = "127.0.0.1"
WEB_PORT = 5000

# HuggingFace
HF_TOKEN = os.environ.get("HF_TOKEN", "")  # Optional: set for higher rate limits

# Torrent settings
DEFAULT_TRACKERS = [
    "udp://tracker.opentrackr.org:1337/announce",
    "udp://tracker.openbittorrent.com:6969/announce",
    "https://tracker.gbitt.info:443/announce",
    "udp://exodus.desync.com:6969/announce",
]

# Index settings
INDEX_PAGE_SIZE = 50
