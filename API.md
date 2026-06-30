# AI-SHIP — REST + MCP API Reference

## REST API

Base URL: `http://localhost:5000`

### Health

```
GET /health
→ {status: "ok", service: "ai-ship", version: "1.0.0"}
```

### Mirror Index

```
GET /api/models?q=&p=0&limit=30
→ {ok: true, items: [...], total: N, page: 0, pages: N}

GET /api/datasets?q=&p=0&limit=30
→ {ok: true, items: [...], total: N, page: 0}

GET /api/items/<slug>
→ {ok: true, item: {...}}  or 404

GET /api/stats
→ {ok: true, models: N, datasets: N, downloaded: N, total_size_bytes: N, total_size_gb: N}
```

### HuggingFace Search

```
GET /api/hf/search/models?q=llama&limit=10
GET /api/hf/search/datasets?q=python&limit=10
→ {ok: true, results: [{id, downloads, tags, author}, ...]}
```

### Download / Register

```
POST /api/download
Content-Type: application/json
{type: "model", repo_id: "openai/whisper-tiny"}
→ {ok: true, id: 1, path: "/data/models/openai_whisper-tiny", size_bytes: N}

POST /api/register
Content-Type: application/json
{type: "model", repo_id: "meta-llama/Llama-3.2-1B", title: "Llama 3.2 1B"}
→ {ok: true, id: 2}
```

### Federation (Gitlawb)

```
GET  /api/federation/search?q=llama&limit=10
→ {ok: true, results: [...], note?: "..."}

POST /api/federation/announce
→ {ok: true, announced: N, items: [...]}

GET  /api/federation/health
→ {ok: true, status: "ok"}  or  {ok: true, status: "error", detail: "..."}
```

---

## MCP Server

Start: `python scripts/mcp_server.py`

Configure in your MCP client:
```json
{
  "mcpServers": {
    "ai-ship": {
      "command": "python",
      "args": ["C:/Users/franz/Desktop/ai-ship/scripts/mcp_server.py"]
    }
  }
}
```

### Tools

| Tool | Arguments | Description |
|---|---|---|
| `hf_search_models` | `query: string, limit?: int` | Search HuggingFace models |
| `hf_search_datasets` | `query: string, limit?: int` | Search HuggingFace datasets |
| `ship_list_models` | `search?: string, limit?: int, offset?: int` | List mirrored models |
| `ship_list_datasets` | `search?: string, limit?: int, offset?: int` | List mirrored datasets |
| `ship_get_model` | `slug: string` | Get model details by slug |
| `ship_stats` | `{}` | Mirror statistics |
| `ship_download` | `repo_id: string, item_type: "model"\|"dataset"` | Download and register |
| `ship_federated_search` | `query?: string, limit?: int` | Search federated peers |

---

## CLI

```bash
python scripts/cli.py search "stable diffusion" --limit 5
python scripts/cli.py models --search llama --limit 10
python scripts/cli.py datasets
python scripts/cli.py download openai/whisper-tiny --type model
python scripts/cli.py stats
python scripts/cli.py federation health
python scripts/cli.py federation search llama
python scripts/cli.py federation announce
python scripts/cli.py serve --port 5000
```

---

## Example: One-command mirror

```bash
# Register a model (no download)
curl -X POST http://localhost:5000/api/register \
  -H "Content-Type: application/json" \
  -d '{"type": "model", "repo_id": "meta-llama/Llama-3.2-1B"}'

# Download and mirror
curl -X POST http://localhost:5000/api/download \
  -H "Content-Type: application/json" \
  -d '{"type": "model", "repo_id": "openai/whisper-tiny"}'
```
