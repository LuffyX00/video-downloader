from fastapi.testclient import TestClient

from app.main import app


def test_health():
    with TestClient(app) as client:
        res = client.get("/api/v1/health")
        assert res.status_code == 200
        assert res.json()["status"] == "ok"


def test_rejects_non_youtube_url():
    with TestClient(app) as client:
        res = client.post("/api/v1/videos/info", json={"url": "https://example.com/video"})
        assert res.status_code == 400
        assert res.json()["error"]["code"] == "invalid_url"


def test_unknown_job_returns_404():
    with TestClient(app) as client:
        res = client.get("/api/v1/downloads/" + "a" * 32)
        assert res.status_code == 404


def test_malformed_job_id_rejected():
    with TestClient(app) as client:
        res = client.get("/api/v1/downloads/../../etc/passwd")
        assert res.status_code in (404, 422)
