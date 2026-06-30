"""
AI-SHIP — Tests
Run: python -m pytest tests/
"""
import pytest, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# ─── Fixtures ──────────────────────────────────────────────────────────────

@pytest.fixture
def app():
    os.environ.setdefault("HF_TOKEN", "")
    os.environ.setdefault("GITLAWB_NODE_URL", "http://localhost:7545")
    from scripts.api import app as flask_app
    flask_app.config["TESTING"] = True
    return flask_app

@pytest.fixture
def client(app):
    return app.test_client()

# ─── Health ────────────────────────────────────────────────────────────────

class TestHealth:
    def test_health(self, client):
        r = client.get("/health")
        assert r.status_code == 200
        data = r.get_json()
        assert data["status"] == "ok"
        assert data["service"] == "ai-ship"

# ─── Stats ─────────────────────────────────────────────────────────────────

    def test_stats(self, client):
        r = client.get("/api/stats")
        assert r.status_code == 200
        data = r.get_json()
        assert "models" in data
        assert "datasets" in data

# ─── Models / Datasets ─────────────────────────────────────────────────────

    def test_list_models_empty(self, client):
        r = client.get("/api/models")
        assert r.status_code == 200
        data = r.get_json()
        assert "items" in data
        assert isinstance(data["items"], list)

    def test_list_datasets_empty(self, client):
        r = client.get("/api/datasets")
        assert r.status_code == 200
        data = r.get_json()
        assert "items" in data

# ─── HuggingFace Search ────────────────────────────────────────────────────

    def test_hf_search_models(self, client):
        r = client.get("/api/hf/search/models?q=llama&limit=3")
        assert r.status_code == 200
        data = r.get_json()
        assert data["ok"] is True
        assert "results" in data

    def test_hf_search_datasets(self, client):
        r = client.get("/api/hf/search/datasets?q=python&limit=3")
        assert r.status_code == 200
        data = r.get_json()
        assert data["ok"] is True

# ─── Download / Register ──────────────────────────────────────────────────

    def test_register_model(self, client):
        r = client.post("/api/register",
                        json={"type": "model", "repo_id": "openai/tiny-random"})
        assert r.status_code == 200
        data = r.get_json()
        assert data["ok"] is True
        assert "id" in data

    def test_register_requires_fields(self, client):
        r = client.post("/api/register", json={})
        assert r.status_code == 400

    def test_download_invalid_type(self, client):
        r = client.post("/api/download", json={"type": "invalid", "repo_id": "x"})
        assert r.status_code == 400

# ─── Federation ────────────────────────────────────────────────────────────

    def test_federation_search(self, client):
        r = client.get("/api/federation/search?q=llama")
        assert r.status_code == 200
        data = r.get_json()
        assert "results" in data

    def test_federation_announce(self, client):
        r = client.post("/api/federation/announce")
        assert r.status_code == 200
        data = r.get_json()
        assert "announced" in data

    def test_federation_health(self, client):
        r = client.get("/api/federation/health")
        assert r.status_code == 200
