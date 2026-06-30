#!/usr/bin/env python3
"""
AI-SHIP CLI
===========
Command-line interface for AI-SHIP.

Usage:
  python scripts/cli.py search "llama 3"
  python scripts/cli.py list models --limit 10
  python scripts/cli.py list datasets
  python scripts/cli.py download openai/whisper-tiny
  python scripts/cli.py stats
  python scripts/cli.py federation search "stable diffusion"
  python scripts/cli.py federation announce
  python scripts/cli.py federation health
  python scripts/cli.py serve         # start the web UI

Install shortcuts (optional):
  pip install -e .   # then just:  ai-ship search "llama"
"""
import argparse, json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from db import get_all, get_by_slug, stats, count_items, add_or_get, mark_downloaded
from downloader import list_hf_models, list_hf_datasets, download_model, download_dataset
from config import WEB_HOST, WEB_PORT

def green(t): return f"\033[92m{t}\033[0m"
def red(t):   return f"\033[91m{t}\033[0m"
def blue(t):  return f"\033[94m{t}\033[0m"
def dim(t):   return f"\033[2m{t}\033[0m"

def cmd_search(args):
    q     = args.query
    limit = args.limit
    print(f"{blue('Searching HuggingFace for:')} {q}\n")
    models   = list_hf_models(query=q, limit=limit)
    datasets  = list_hf_datasets(query=q, limit=limit)
    if not models and not datasets:
        print("No results found.")
        return
    if models:
        print(f"  {green('Models:')}")
        for m in models:
            print(f"    {m['id']}")
            print(f"      downloads: {m.get('downloads', 0):,}  author: {m.get('author','?')}")
            print()
    if datasets:
        print(f"  {green('Datasets:')}")
        for d in datasets:
            print(f"    {d['id']}")
            print(f"      downloads: {d.get('downloads', 0):,}")

def cmd_list(args):
    item_type = args.type or ("dataset" if "dataset" in args.type else "model")
    itype = "dataset" if args.command == "datasets" else "model"
    limit = min(args.limit, 100)
    items = get_all(item_type=itype, search=args.search or "", limit=limit)
    total = count_items(item_type=itype)
    label = f"{'Dataset' if itype == 'dataset' else 'Model'}s"
    print(f"{blue(f'AI-SHIP {label}')}: {total} total\n")
    for item in items:
        downloaded = "✓" if item.get("downloaded") else " "
        size_gb = f"{item['size_bytes']/1e9:.2f} GB" if item.get("size_bytes") else "—"
        print(f"  [{downloaded}] {item['repo_id']}  {dim(size_gb)}")
    if not items:
        print(f"  {dim('No items yet.')}")

def cmd_download(args):
    repo_id  = args.repo_id
    itype    = args.type or "model"
    print(f"{blue(f'Downloading:')} {repo_id} ({itype})\n")
    if itype == "model":
        path, result = download_model(repo_id)
    else:
        path, result = download_dataset(repo_id)
    if path is None:
        print(f"  {red('Error:')} {result}")
        sys.exit(1)
    item_id = add_or_get(itype, repo_id, repo_id.split("/")[-1],
                         filename=repo_id.replace("/", "_"),
                         size_bytes=os.path.getsize(path) if os.path.exists(path) else 0)
    mark_downloaded(item_id)
    print(f"  {green('Downloaded and registered:')} {path}")
    print(f"  {green('Item ID:')} {item_id}")

def cmd_stats(args):
    s = stats()
    size_gb = round(s["total_size_bytes"] / 1e9, 2) if s["total_size_bytes"] else 0
    print(f"{blue('AI-SHIP Mirror Stats')}\n")
    print(f"  Models:    {s['models']}")
    print(f"  Datasets:  {s['datasets']}")
    print(f"  Downloaded: {s['downloaded']}")
    print(f"  Total size: {size_gb} GB")

def cmd_federation(args):
    from scripts.gitlawb_bridge import AIShipBridge
    bridge = AIShipBridge()

    if args.fed_cmd == "health":
        r = bridge.check()
        print(json.dumps(r, indent=2))
        return

    if args.fed_cmd == "announce":
        print(f"{blue('Announcing local index to gitlawb peers...')}\n")
        results = bridge.announce_local_index()
        print(f"  {green('Announced:')} {len(results)} items")
        return

    if args.fed_cmd == "search":
        q     = args.query or ""
        limit = args.limit
        print(f"{blue('Federated search:')} {q or '(all)'}\n")
        results = bridge.discover(query=q, limit=limit)
        if not results:
            print(f"  {dim('No federated results. Is your gitlawb node running?')}")
            return
        for r in results:
            print(f"  {r}")
        return

def cmd_serve(args):
    import subprocess
    port = args.port
    print(f"{blue('Starting AI-SHIP web UI at:')} http://localhost:{port}")
    print(f"{dim('Press Ctrl+C to stop')}\n")
    subprocess.run([sys.executable, "app.py"], cwd=os.path.dirname(os.path.dirname(__file__)))

def main():
    parser = argparse.ArgumentParser(prog="ai-ship",
                                     description="AI-SHIP CLI — decentralized AI model mirror")
    sub = parser.add_subparsers(dest="command")

    # search
    p = sub.add_parser("search", help="Search HuggingFace")
    p.add_argument("query")
    p.add_argument("--limit", "-n", type=int, default=10)

    # list models / list datasets
    for cmd, help_txt in [("models", "List mirrored models"),
                           ("datasets", "List mirrored datasets")]:
        p = sub.add_parser(cmd, help=help_txt)
        p.add_argument("--search", "-q", default="")
        p.add_argument("--limit", "-n", type=int, default=30)

    # download
    p = sub.add_parser("download", help="Download a model or dataset from HuggingFace")
    p.add_argument("repo_id")
    p.add_argument("--type", choices=["model", "dataset"], default="model")

    # stats
    sub.add_parser("stats", help="Show mirror statistics")

    # federation
    p = sub.add_parser("federation", help="Federation via gitlawb")
    p.add_argument("fed_cmd", choices=["health", "announce", "search"])
    p.add_argument("--query", "-q", default="")
    p.add_argument("--limit", "-n", type=int, default=10)

    # serve
    p = sub.add_parser("serve", help="Start the web UI")
    p.add_argument("--port", type=int, default=WEB_PORT)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    if args.command in ("models", "datasets", "list"):
        args.type = args.command
        args.command = "list"
        cmd_list(args)
    elif args.command == "search":
        cmd_search(args)
    elif args.command == "download":
        cmd_download(args)
    elif args.command == "stats":
        cmd_stats(args)
    elif args.command == "federation":
        cmd_federation(args)
    elif args.command == "serve":
        cmd_serve(args)

if __name__ == "__main__":
    main()
