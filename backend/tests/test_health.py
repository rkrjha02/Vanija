from fastapi.testclient import TestClient

from app.main import app


def test_health_returns_ok_without_auth():
    with TestClient(app) as client:
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}
