# AI-SHIP Todo

## Done

- [x] Core app: Flask web UI, SQLite index, HuggingFace downloader
- [x] REST API: 14 endpoints with CORS
- [x] MCP server: 8 tools for AI agents
- [x] CLI: search, list, download, stats, federation commands
- [x] Gitlawb bridge: federated model announcement and discovery
- [x] FTS5 full-text search index
- [x] Model detail page: full metadata, HF source, badges, actions
- [x] Auto-sync: mirror trending HuggingFace models
- [x] Docker: Dockerfile + docker-compose.yml
- [x] CI: GitHub Actions — pytest + API smoke + ruff lint
- [x] Docs: README, API, INTEGRATION, CONTRIBUTING, ACCREDITATION, INSTALL
- [x] Smoke tests: all verified live against real HF API

## To Do

- [ ] CI: auto-test downloader against real HF small model
- [ ] Prometheus metrics endpoint (`GET /metrics`)
- [ ] Peer live list API (`GET /api/peers`)
- [ ] Dataset streaming download support
- [ ] Web of trust — Ed25519 DID signatures on model metadata
- [ ] IPNS integration for persistent model index name

## Nice to Have

- [ ] Claude Desktop MCP config snippet in README
- [ ] Civitai / Kaggle as additional model sources
- [ ] Model ratings and comments
- [ ] Demo video script
- [ ] Raspberry Pi seeding guide
