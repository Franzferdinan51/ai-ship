#!/usr/bin/env bash
# AI-SHIP — 90-Second Demo
# Run this on any machine with Python 3.10+ to see AI-SHIP in action.

set -e

echo "╔══════════════════════════════════════╗"
echo "║      AI-SHIP — 90 Second Demo       ║"
echo "╚══════════════════════════════════════╝"
echo ""

# ── 1. Check deps ──────────────────────────────────────────────────────────
echo "[1/6] Checking dependencies..."
python3 -c "import flask, requests, huggingface_hub; print('  All deps OK')" 2>/dev/null || {
  echo "  Installing deps..."
  pip install -q -r requirements.txt
}
echo ""

# ── 2. Start server ──────────────────────────────────────────────────────
echo "[2/6] Starting AI-SHIP web server on :5000..."
python3 app.py &
SERVER_PID=$!
sleep 3
echo "  Server running (PID $SERVER_PID)"
echo ""

# ── 3. Health check ──────────────────────────────────────────────────────
echo "[3/6] Health check..."
STATUS=$(curl -s http://localhost:5000/health | python3 -c "import sys,json; print(json.load(sys.stdin)['status'])")
echo "  Status: $STATUS"
echo ""

# ── 4. Search HuggingFace ────────────────────────────────────────────────
echo "[4/6] Searching HuggingFace for 'llama 3'..."
curl -s "http://localhost:5000/api/hf/search/models?q=llama&limit=3" \
  | python3 -c "
import sys,json
d=json.load(sys.stdin)
for m in d.get('results',[]):
    print(f\"  - {m['id']} ({m.get('downloads',0):,} downloads)\"
"
echo ""

# ── 5. Register a model ─────────────────────────────────────────────────
echo "[5/6] Registering a model in the local index..."
RESULT=$(curl -s -X POST http://localhost:5000/api/register \
  -H "Content-Type: application/json" \
  -d '{"type":"model","repo_id":"openai/whisper-tiny"}')
echo "  $RESULT"
echo ""

# ── 6. Browse mirrored models ───────────────────────────────────────────
echo "[6/6] Local mirrored models..."
curl -s http://localhost:5000/api/models \
  | python3 -c "
import sys,json
d=json.load(sys.stdin)
print(f\"  Total mirrored: {d.get('total',0)}\")
for m in d.get('items',[])[:5]:
    dl='✓' if m.get('downloaded') else '○'
    print(f\"  {dl} {m['repo_id']}\")
"
echo ""

# ── Done ─────────────────────────────────────────────────────────────────
echo "══════════════════════════════════════"
echo "Demo complete! Server still running at:"
echo "  Web UI:  http://localhost:5000"
echo "  API:     http://localhost:5000/api/"
echo ""
echo "Press Ctrl+C to stop the server."
echo ""

# Keep server alive, allow Ctrl+C
wait $SERVER_PID
