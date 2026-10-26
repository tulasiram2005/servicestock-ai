from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db import schema as db
from app.db.store import Store
from app.ingest.seed import seed
from app.main import create_app
from app.services import publish


def test_pagination_admin_budget_and_job_idor(settings):
    store = Store("sqlite://")
    db.metadata.create_all(store.engine)
    seed(store)
    publish(store, Path(__file__).resolve().parents[2] / "results")
    with TestClient(create_app(settings, store_override=store)) as client:
        demo = client.post("/api/auth/login", json={"username": "demo", "password": settings.demo_password}).json()["access_token"]
        admin = client.post("/api/auth/login", json={"username": "admin", "password": settings.admin_password}).json()["access_token"]
        viewer_headers, admin_headers = {"Authorization": "Bearer " + demo}, {"Authorization": "Bearer " + admin}
        first = client.get("/api/parts?limit=2", headers=viewer_headers).json()
        second = client.get("/api/parts", params={"limit": 2, "cursor": first["next_cursor"]}, headers=viewer_headers).json()
        assert first["items"][-1]["id"] < second["items"][0]["id"]
        assert client.get("/api/admin/usage", headers=viewer_headers).status_code == 403
        assert client.get("/api/admin/usage", headers=admin_headers).json()["row_counts"]["parts"] == 24
        body = {"idempotency_key": "test-job-key", "service_level": 0.95}
        assert client.post("/api/whatif", json=body, headers=viewer_headers).status_code == 403
        response = client.post("/api/whatif", json=body, headers=admin_headers)
        assert response.status_code == 200
        job_id = response.json()["job_id"]
        assert client.get("/api/jobs/" + job_id, headers=viewer_headers).status_code == 404
        assert client.get("/api/jobs/" + job_id, headers=admin_headers).status_code == 200
