"""AI-SHIP — Auto-Sync Trending HuggingFace Models"""
import argparse
from datetime import datetime
from downloader import list_hf_models, download_model, get_dir_size

def sync_trending(limit=20, dry_run=True):
    """Pull trending models from HuggingFace. Pass --no-dry-run to actually download."""
    print(f"[{datetime.now().isoformat()}] Fetching top {limit} trending models...")
    models = list_hf_models(limit=limit)
    results = []
    for m in models:
        repo_id = m["id"]
        dl = m.get("downloads", 0)
        if dry_run:
            print(f"  [DRY] {repo_id} ({dl:,} downloads)")
            results.append({"repo_id": repo_id, "status": "dry"})
            continue
        try:
            print(f"  Downloading {repo_id}...")
            path, result = download_model(repo_id)
            if path is None:
                print(f"  FAILED: {repo_id} — {result}")
                results.append({"repo_id": repo_id, "status": "error", "detail": result})
            else:
                size = get_dir_size(path)
                print(f"  OK: {repo_id} — {size/1e9:.2f} GB")
                results.append({"repo_id": repo_id, "status": "ok", "path": path, "size": size})
        except Exception as e:
            print(f"  ERROR: {repo_id} — {e}")
            results.append({"repo_id": repo_id, "status": "error", "detail": str(e)})
    return results

if __name__ == "__main__":
    p = argparse.ArgumentParser(description="AI-SHIP Auto-Sync")
    p.add_argument("--limit", "-n", type=int, default=20)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--no-dry-run", dest="dry_run", action="store_false")
    args = p.parse_args()
    results = sync_trending(limit=args.limit, dry_run=args.dry_run)
    ok = sum(1 for r in results if r["status"] == "ok")
    print(f"\nDone. {ok}/{len(results)} synced.")
