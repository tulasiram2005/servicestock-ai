from pathlib import Path
import pytest

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db import schema as db
from app.db.store import Store
from app.ingest.seed import seed
from app.main import create_app
from app.services import publish
from app.services import artifact


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
        configuration = {"model_id": "MODEL-1", "before_options": ["AC"], "options": ["AC", "SENSOR"]}
        assert client.post("/api/configurations/impact", json=configuration).status_code == 401
        impact = client.post("/api/configurations/impact", json=configuration, headers=viewer_headers)
        assert impact.status_code == 200
        assert impact.json()["cost_change_usd"] == 59
        assert client.get("/api/admin/usage", headers=admin_headers).json()["row_counts"]["parts"] == 24
        body = {"idempotency_key": "test-job-key", "service_level": 0.95}
        assert client.post("/api/whatif", json=body, headers=viewer_headers).status_code == 403
        response = client.post("/api/whatif", json=body, headers=admin_headers)
        assert response.status_code == 200
        job_id = response.json()["job_id"]
        assert client.get("/api/jobs/" + job_id, headers=viewer_headers).status_code == 404
        assert client.get("/api/jobs/" + job_id, headers=admin_headers).status_code == 200
        assert client.get("/api/admin/jobs", headers=viewer_headers).status_code == 403
        jobs = client.get("/api/admin/jobs", headers=admin_headers).json()
        assert job_id in {job["id"] for job in jobs}
        assert all(set(job) == {"id", "kind", "status", "progress", "attempts", "created_at"} for job in jobs)


@pytest.mark.parametrize("order", ["asc", "desc"])
def test_segment_pagination_has_no_duplicates_or_missing_parts(settings, order):
    store = Store("sqlite://")
    db.metadata.create_all(store.engine)
    seed(store)
    publish(store, Path(__file__).resolve().parents[2] / "results")
    expected = sorted([part["part_id"] for part in artifact(store, "benchmark")["parts"] if part["abc"] == "A"], reverse=order == "desc")
    with TestClient(create_app(settings, store_override=store)) as client:
        token = client.post("/api/auth/login", json={"username": "demo", "password": settings.demo_password}).json()["access_token"]
        headers = {"Authorization": "Bearer " + token}
        cursor, found = "", []
        for _ in range(30):
            result = client.get("/api/parts", params={"segment": "A", "order": order, "limit": 2, "cursor": cursor}, headers=headers)
            assert result.status_code == 200
            body = result.json()
            assert all(part["segment"] == "A" for part in body["items"])
            found.extend(part["id"] for part in body["items"])
            cursor = body["next_cursor"]
            if cursor is None:
                break
        assert found == expected
        for params in ({"order": "random"}, {"segment": "Z"}):
            assert client.get("/api/parts", params=params, headers=headers).status_code == 422
        result = client.get("/api/parts", params={"query": expected[0], "segment": "A"}, headers=headers).json()
        assert [part["id"] for part in result["items"]] == [expected[0]]
