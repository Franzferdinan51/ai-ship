"""
AI-SHIP Web UI
Decentralized mirror for AI models and datasets — built on Gitlawb.
Run: python app.py
"""
import os
from flask import Flask, render_template, request, jsonify
from db import get_all, get_by_slug, add_or_get, stats, count_items, mark_downloaded
from downloader import download_model, download_dataset, list_hf_models, list_hf_datasets
from config import WEB_HOST, WEB_PORT, MODELS_DIR, DATASETS_DIR

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True

# ─── Pages ───────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    s = stats()
    return render_template('index.html', stats=s)

@app.route('/models')
def models_page():
    search = request.args.get('q', '')
    page   = int(request.args.get('p', 0))
    items  = get_all(item_type='model', search=search, limit=30, offset=page*30)
    total  = count_items(item_type='model')
    return render_template('model_list.html', items=items, total=total,
                           page=page, search=search, item_type='models')

@app.route('/datasets')
def datasets_page():
    search = request.args.get('q', '')
    page   = int(request.args.get('p', 0))
    items  = get_all(item_type='dataset', search=search, limit=30, offset=page*30)
    total  = count_items(item_type='dataset')
    return render_template('model_list.html', items=items, total=total,
                           page=page, search=search, item_type='datasets')

@app.route('/item/<slug>')
def item_page(slug):
    item = get_by_slug(slug)
    if not item:
        return "Not found", 404
    return render_template('model_detail.html', item=item)

# ─── Health ──────────────────────────────────────────────────────────────────

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'service': 'ai-ship', 'version': '1.0.0'})

# ─── API ─────────────────────────────────────────────────────────────────────

@app.route('/api/stats')
def api_stats():
    return jsonify(stats())

@app.route('/api/models')
def api_models():
    """List all mirrored models."""
    models = get_all(item_type='model', limit=100)
    return jsonify({'items': models, 'total': len(models)})

@app.route('/api/datasets')
def api_datasets():
    """List all mirrored datasets."""
    datasets = get_all(item_type='dataset', limit=100)
    return jsonify({'items': datasets, 'total': len(datasets)})

@app.route('/api/search', methods=['GET'])
def api_search():
    """Full-text search over mirrored models and datasets."""
    q     = request.args.get('q', '')
    limit = min(int(request.args.get('limit', 20)), 100)
    page  = max(int(request.args.get('p', 0)), 0)
    itype = request.args.get('type', None)  # 'model', 'dataset', or None for all
    offset = page * limit

    # Try FTS first, fall back to LIKE
    try:
        from scripts.full_text_search import search_fts
        results = search_fts(q, item_type=itype, limit=limit)
    except Exception:
        # Fallback to LIKE search
        results = get_all(item_type=itype, search=q, limit=limit, offset=offset)

    return jsonify({
        'ok': True,
        'query': q,
        'item_type': itype,
        'items': results,
        'limit': limit,
        'page': page,
    })

@app.route('/api/search/models', methods=['GET'])
def api_search_models():
    return api_search()

@app.route('/api/search/datasets', methods=['GET'])
def api_search_datasets():
    return api_search()

@app.route('/api/download', methods=['POST'])
def api_download():
    """Download a model or dataset from HuggingFace and register it in the index."""
    data     = request.json
    item_type = data.get('type')    # 'model' or 'dataset'
    repo_id  = data.get('repo_id')
    if not repo_id or item_type not in ('model', 'dataset'):
        return jsonify({'error': 'Invalid request'}), 400

    if item_type == 'model':
        path, result = download_model(repo_id)
    else:
        path, result = download_dataset(repo_id)

    if path is None:
        return jsonify({'error': result}), 500

    dest_dir = MODELS_DIR if item_type == 'model' else DATASETS_DIR
    name = repo_id.replace('/', '_')
    item_id = add_or_get(
        item_type, repo_id,
        title=repo_id.split('/')[-1],
        filename=name,
        size_bytes=os.path.getsize(path) if os.path.exists(path) else 0,
    )
    mark_downloaded(item_id)
    return jsonify({
        'ok': True,
        'path': path,
        'id': item_id,
    })

@app.route('/api/register', methods=['POST'])
@app.route('/api/add', methods=['POST'])
def api_register():
    """Register a HuggingFace model or dataset in the index without downloading."""
    data     = request.json
    item_type = data.get('type')
    repo_id  = data.get('repo_id')
    title    = data.get('title', repo_id)
    if not item_type or not repo_id:
        return jsonify({'error': 'Invalid'}), 400
    item_id = add_or_get(item_type, repo_id, title, f'HF:{repo_id}')
    return jsonify({'ok': True, 'id': item_id})

@app.route('/api/hf/search/models', methods=['GET'])
def api_hf_models():
    q     = request.args.get('q', '')
    limit = min(int(request.args.get('limit', 10)), 50)
    results = list_hf_models(query=q, limit=limit)
    return jsonify({'ok': True, 'results': results})

@app.route('/api/hf/search/datasets', methods=['GET'])
def api_hf_datasets():
    q     = request.args.get('q', '')
    limit = min(int(request.args.get('limit', 10)), 50)
    results = list_hf_datasets(query=q, limit=limit)
    return jsonify({'ok': True, 'results': results})

if __name__ == '__main__':
    print(f"Starting AI-SHIP at http://{WEB_HOST}:{WEB_PORT}")
    app.run(host=WEB_HOST, port=WEB_PORT, debug=True)
