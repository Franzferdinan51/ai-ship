"""
AI-SHIP — HuggingFace Downloader
Downloads models/datasets from HuggingFace and registers them in the local index.
"""
import os, hashlib, time
from huggingface_hub import snapshot_download, hf_hub_download
from config import MODELS_DIR, DATASETS_DIR, HF_TOKEN

def download_model(repo_id, filename=None, dest_dir=None):
    """
    Download a model from HuggingFace Hub.
    Returns (local_path, size_bytes).
    """
    dest = dest_dir or MODELS_DIR
    try:
        local_path = snapshot_download(
            repo_id=repo_id,
            local_dir=os.path.join(dest, repo_id.replace('/', '_')),
            ignore_patterns=["*.msgpack", "*.h5", "*.ot"],
            token=HF_TOKEN or None,
            resume_download=True,
        )
        size = get_dir_size(local_path)
        return local_path, size
    except Exception as e:
        return None, str(e)

def download_dataset(repo_id, filename=None, dest_dir=None):
    """
    Download a dataset from HuggingFace Hub.
    """
    dest = dest_dir or DATASETS_DIR
    try:
        from huggingface_hub import hf_hub_download as dl
        if filename:
            path = dl(repo_id=repo_id, filename=filename, token=HF_TOKEN or None)
            return path, os.path.getsize(path)
        else:
            from datasets import load_dataset
            ds = load_dataset(repo_id, split="train", token=HF_TOKEN or None)
            local_dir = os.path.join(dest, repo_id.replace('/', '_'))
            ds.save_to_disk(local_dir)
            return local_dir, get_dir_size(local_dir)
    except Exception as e:
        return None, str(e)

def get_dir_size(path):
    total = 0
    for dirpath, dirnames, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            try:
                total += os.path.getsize(fp)
            except OSError:
                pass
    return total

def sha256_file(filepath):
    h = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()

def list_hf_models(query=None, limit=20):
    """
    Search HuggingFace for models using the API.
    Returns list of dicts with name, id, downloads, tags.
    """
    from huggingface_hub import list_models
    try:
        models = list_models(search=query or "", limit=limit)
        return [
            {
                "id": m.id,
                "downloads": getattr(m, 'downloads', 0),
                "tags": list(getattr(m, 'tags', [])[:5]),
                "author": m.id.split('/')[0] if '/' in m.id else m.id,
            }
            for m in models
        ]
    except Exception as e:
        return [{"error": str(e)}]

def list_hf_datasets(query=None, limit=20):
    """
    Search HuggingFace for datasets.
    """
    from huggingface_hub import list_datasets
    try:
        datasets = list_datasets(search=query or "", limit=limit)
        return [
            {
                "id": d.id,
                "downloads": getattr(d, 'downloads', 0),
                "tags": list(getattr(d, 'tags', [])[:5]),
            }
            for d in datasets
        ]
    except Exception as e:
        return [{"error": str(e)}]
