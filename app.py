"""
AI-SHIP — Web UI
Decentralized mirror for AI models and datasets.
Run: python app.py
"""
import os, sys
from flask import Flask, render_template, request, jsonify, send_file
from db import get_all, get_by_slug, add_or_get, stats, count_items, mark_seeding, mark_downloaded
from downloader import download_model, download_dataset, list_hf_models, list_hf_datasets
from torrent import create_and_save
from config import WEB_HOST, WEB_PORT, MODELS_DIR, DATASETS_DIR, TORRENTS_DIR

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

# ─── API ──────────────────────────────────────────────────────────────────────

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
    data = request.json
    item_type = data.get('type')   # 'model' or 'dataset'
    repo_id   = data.get('repo_id')
    if not repo_id or item_type not in ('model', 'dataset'):
        return jsonify({'error': 'Invalid request'}), 400

    if item_type == 'model':
        path, result = download_model(repo_id)
    else:
        path, result = download_dataset(repo_id)

    if path is None:
        return jsonify({'error': result}), 500

    # Create torrent for downloaded content
    dest_dir = MODELS_DIR if item_type == 'model' else DATASETS_DIR
    name = repo_id.replace('/', '_')
    try:
        t_path, magnet = create_and_save(path, name, output_dir=TORRENTS_DIR)
        item_id = add_or_get(item_type, repo_id, repo_id.split('/')[-1],
                             name, os.path.getsize(path),
                             magnet=magnet, torrent_file=t_path)
        mark_downloaded(item_id)
        return jsonify({'ok': True, 'path': path, 'magnet': magnet,
                        'torrent': t_path})
    except Exception as e:
        return jsonify({'ok': True, 'path': path, 'error': str(e)})

@app.route('/api/add', methods=['POST'])
def api_add():
    """Register a model/dataset without downloading — just index it."""
    data = request.json
    item_type = data.get('type')
    repo_id   = data.get('repo_id')
    title     = data.get('title', repo_id)
    if not item_type or not repo_id:
        return jsonify({'error': 'Invalid'}), 400
    item_id = add_or_get(item_type, repo_id, title, f'HF:{repo_id}')
    return jsonify({'ok': True, 'id': item_id})

@app.route('/torrents/<slug>')
def serve_torrent(slug):
    item = get_by_slug(slug)
    if not item or not item.get('torrent_file'):
        return "Torrent not found", 404
    return send_file(item['torrent_file'],
                     as_attachment=True,
                     download_name=f"{slug}.torrent")

if __name__ == '__main__':
    print(f"Starting AI-SHIP at http://{WEB_HOST}:{WEB_PORT}")
    app.run(host=WEB_HOST, port=WEB_PORT, debug=True)
