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
    return render_template('item.html', item=item)

# ─── API ─────────────────────────────────────────────────────────────────────

@app.route('/api/stats')
def api_stats():
    return jsonify(stats())

@app.route('/api/search')
def api_search():
    q = request.args.get('q', '')
    models   = list_hf_models(query=q, limit=10)
    datasets = list_hf_datasets(query=q, limit=10)
    return jsonify({'models': models, 'datasets': datasets})

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

@app.route('/api/add', methods=['POST'])
def api_add():
    """Register a HuggingFace model or dataset in the index without downloading."""
    data     = request.json
    item_type = data.get('type')
    repo_id  = data.get('repo_id')
    title    = data.get('title', repo_id)
    if not item_type or not repo_id:
        return jsonify({'error': 'Invalid'}), 400
    item_id = add_or_get(item_type, repo_id, title, f'HF:{repo_id}')
    return jsonify({'ok': True, 'id': item_id})

if __name__ == '__main__':
    print(f"Starting AI-SHIP at http://{WEB_HOST}:{WEB_PORT}")
    app.run(host=WEB_HOST, port=WEB_PORT, debug=True)
