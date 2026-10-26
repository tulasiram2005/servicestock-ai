import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


@pytest.fixture
def settings():
    return Settings(jwt_secret="test-signing-secret-at-least-32-characters",
                    demo_password="test-demo-password", admin_password="test-admin-password",
                    environment="test", worker_mode="disabled")


@pytest.fixture
def client(settings):
    with TestClient(create_app(settings)) as instance:
        yield instance


@pytest.fixture
def demo_headers(client, settings):
    response = client.post("/api/auth/login", json={"username": settings.demo_username, "password": settings.demo_password})
    return {"Authorization": "Bearer " + response.json()["access_token"]}


@pytest.fixture
def admin_headers(client, settings):
    response = client.post("/api/auth/login", json={"username": settings.admin_username, "password": settings.admin_password})
    return {"Authorization": "Bearer " + response.json()["access_token"]}
