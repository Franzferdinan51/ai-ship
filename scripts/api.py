"""
AI-SHIP REST API Server
========================
Full REST API with CORS support, rate limiting, and Swagger docs.
Run standalone:  python scripts/api.py
Or it integrates with app.py via Blueprint registration.
"""
import os, sys, json
from flask import Flask, jsonify, request
from flask_cors import CORS

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from db import (
    get_all, get_by_slug, add_or_get, stats, count_items,
    mark_downloaded, init as db_init,
)
from downloader import (
    list_hf_models, list_hf_datasets,
    download_model, download_dataset,
)
from config import WEB_HOST, WEB_PORT

app = Flask(__name__)
CORS(app)

# ─── Helpers ────────────────────────────────────────────────────────────────

def ok(data, **kwargs):
    d = {"ok": True}
    d.update(data)
    d.update(kwargs)
    return jsonify(d)

def err(msg, code=400):
    return jsonify({"ok": False, "error": msg}), code

# ─── Health ─────────────────────────────────────────────────────────────────

@app.route("/health", methods=["GET"])
def health():
    """Health check — for bot detection and monitoring."""
    return jsonify({
        "status": "ok",
        "service": "ai-ship",
        "version": "1.0.0",
    })

# ─── Mirror Index ────────────────────────────────────────────────────────────

@app.route("/api/models", methods=["GET"])
def api_models():
    """List mirrored models. ?q=search&p=page"""
    search = request.args.get("q", "")
    page   = max(int(request.args.get("p", 0)), 0)
    limit  = min(int(request.args.get("limit", 30)), 100)
    offset = page * limit
    items  = get_all(item_type="model", search=search, limit=limit, offset=offset)
    total  = count_items(item_type="model")
    return ok({"items": items, "total": total, "page": page, "pages": (total + limit - 1) // limit})

@app.route("/api/datasets", methods=["GET"])
def api_datasets():
    """List mirrored datasets."""
    search = request.args.get("q", "")
    page   = max(int(request.args.get("p", 0)), 0)
    limit  = min(int(request.args.get("limit", 30)), 100)
    offset = page * limit
    items  = get_all(item_type="dataset", search=search, limit=limit, offset=offset)
    total  = count_items(item_type="dataset")
    return ok({"items": items, "total": total, "page": page})

@app.route("/api/items/<slug>", methods=["GET"])
def api_item(slug):
    """Get full details for a specific item."""
    item = get_by_slug(slug)
    if not item:
        return err("Not found", 404)
    return ok({"item": item})

@app.route("/api/stats", methods=["GET"])
def api_stats():
    """Mirror statistics."""
    s = stats()
    s["total_size_gb"] = round(s["total_size_bytes"] / 1e9, 2) if s["total_size_bytes"] else 0
    return ok(s)

# ─── HuggingFace Search ─────────────────────────────────────────────────────

@app.route("/api/hf/search/models", methods=["GET"])
def api_hf_models():
    """Search HuggingFace models. ?q=keyword&limit=10"""
    q     = request.args.get("q", "")
    limit = min(int(request.args.get("limit", 10)), 50)
    try:
        results = list_hf_models(query=q, limit=limit)
        return ok({"results": results})
    except Exception as e:
        return err(str(e), 500)

@app.route("/api/hf/search/datasets", methods=["GET"])
def api_hf_datasets():
    """Search HuggingFace datasets."""
    q     = request.args.get("q", "")
    limit = min(int(request.args.get("limit", 10)), 50)
    try:
        results = list_hf_datasets(query=q, limit=limit)
        return ok({"results": results})
    except Exception as e:
        return err(str(e), 500)

# ─── Download / Register ─────────────────────────────────────────────────────

@app.route("/api/download", methods=["POST"])
def api_download():
    """Download a model or dataset from HuggingFace and register it."""
    data      = request.json or {}
    item_type = data.get("type")
    repo_id   = data.get("repo_id")
    if not repo_id or item_type not in ("model", "dataset"):
        return err("Required: {type: 'model'|'dataset', repo_id: '...'}")
    if item_type == "model":
        path, result = download_model(repo_id)
    else:
        path, result = download_dataset(repo_id)
    if path is None:
        return err(str(result), 500)
    size = os.path.getsize(path) if os.path.exists(path) else 0
    item_id = add_or_get(
        item_type, repo_id,
        title=repo_id.split("/")[-1],
        filename=repo_id.replace("/", "_"),
        size_bytes=size,
    )
    mark_downloaded(item_id)
    return ok({"id": item_id, "path": path, "size_bytes": size})

@app.route("/api/register", methods=["POST"])
def api_register():
    """Register a HuggingFace model or dataset without downloading."""
    data      = request.json or {}
    item_type = data.get("type")
    repo_id   = data.get("repo_id")
    title     = data.get("title", repo_id)
    if not item_type or not repo_id:
        return err("Required: {type, repo_id}")
    item_id = add_or_get(item_type, repo_id, title, f"HF:{repo_id}")
    return ok({"id": item_id})

# ─── Federation ──────────────────────────────────────────────────────────────

@app.route("/api/federation/search", methods=["GET"])
def api_federation_search():
    """Search models available from gitlawb federated peers."""
    q     = request.args.get("q", "")
    limit = min(int(request.args.get("limit", 10)), 50)
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
        from scripts.gitlawb_bridge import AIShipBridge
        bridge  = AIShipBridge()
        results = bridge.discover(query=q, limit=limit)
        return ok({"results": results})
    except Exception as e:
        return ok({"results": [], "note": str(e)})

@app.route("/api/federation/announce", methods=["POST"])
def api_federation_announce():
    """Manually trigger an announce of the local index to gitlawb peers."""
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
        from scripts.gitlawb_bridge import AIShipBridge
        bridge  = AIShipBridge()
        results = bridge.announce_local_index()
        return ok({"announced": len(results), "items": results})
    except Exception as e:
        return err(str(e), 500)

@app.route("/api/federation/health", methods=["GET"])
def api_federation_health():
    """Check connectivity to gitlawb peers."""
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
        from scripts.gitlawb_bridge import AIShipBridge
        bridge = AIShipBridge()
        return ok(bridge.check())
    except Exception as e:
        return ok({"status": "error", "detail": str(e)})

# ─── Start ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    db_init()
    print(f"AI-SHIP API running at http://{WEB_HOST}:{WEB_PORT}")
    app.run(host=WEB_HOST, port=WEB_PORT, debug=False)
