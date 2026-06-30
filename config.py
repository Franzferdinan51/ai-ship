"""
AI-SHIP Configuration
"""
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, "models")
DATASETS_DIR = os.path.join(BASE_DIR, "datasets")
TORRENTS_DIR = os.path.join(BASE_DIR, "torrents")
DB_PATH = os.path.join(BASE_DIR, "db", "index.db")

for d in [MODELS_DIR, DATASETS_DIR, TORRENTS_DIR]:
    os.makedirs(d, exist_ok=True)

WEB_HOST = "127.0.0.1"
WEB_PORT = 5000

# HuggingFace token (optional, for higher rate limits)
HF_TOKEN = os.environ.get("HF_TOKEN", "")

# BitTorrent trackers
DEFAULT_TRACKERS = [
    "udp://tracker.opentrackr.org:1337/announce",
    "udp://tracker.openbittorrent.com:6969/announce",
    "https://tracker.gbitt.info:443/announce",
    "udp://exodus.desync.com:6969/announce",
    "https://tracker1.520.jp:443/announce",
]

# Gitlawb node
GITLAWB_NODE_URL = os.environ.get("GITLAWB_NODE_URL", "http://localhost:7545")
GITLAWB_DID = os.environ.get("GITLAWB_DID", "")

INDEX_PAGE_SIZE = 50
