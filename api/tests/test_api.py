from fastapi.testclient import TestClient
import pytest

from app.main import RateLimiter, Settings, create_app


TOKEN = "test-only-token-with-at-least-32-characters"


@pytest.fixture
def client():
    return TestClient(create_app(Settings(api_token=TOKEN)))


def test_health_does_not_expose_configuration(client):
    response = client.get("/health/live")
    assert response.json() == {"status": "ok"}
    assert response.headers["cache-control"] == "no-store"


@pytest.mark.parametrize("headers", [{}, {"Authorization": "Bearer wrong"}])
def test_private_routes_require_valid_token(client, headers):
    assert client.get("/api/status", headers=headers).status_code == 401
    assert client.post("/api/assistant", json={"text": "hello"}, headers=headers).status_code == 401


def test_status_has_no_fabricated_metrics(client):
    response = client.get("/api/status", headers={"Authorization": f"Bearer {TOKEN}"})
    assert response.status_code == 200
    assert response.json()["metrics"] is None
    assert response.json()["database_connected"] is False
    assert TOKEN not in response.text


def test_mock_is_explicit_and_does_not_echo_input(client):
    response = client.post("/api/assistant", json={"text": "private customer data"}, headers={"Authorization": f"Bearer {TOKEN}"})
    assert response.status_code == 200
    assert response.json()["is_mock"] is True
    assert "private customer data" not in response.text


@pytest.mark.parametrize("text", ["", "x" * 4001])
def test_prompt_bounds(client, text):
    assert client.post("/api/assistant", json={"text": text}, headers={"Authorization": f"Bearer {TOKEN}"}).status_code == 422


def test_rate_limit_recovers_after_window():
    current = [0]
    limiter = RateLimiter(limit=2, clock=lambda: current[0])
    assert limiter.allow()
    assert limiter.allow()
    assert not limiter.allow()
    current[0] = 60
    assert limiter.allow()


def test_http_rate_limit(client):
    for attempt in range(30):
        assert client.get("/api/status", headers={"Authorization": f"Bearer {TOKEN}"}).status_code == 200
    assert client.get("/api/status", headers={"Authorization": f"Bearer {TOKEN}"}).status_code == 429


def test_missing_secret_fails_closed(monkeypatch):
    monkeypatch.delenv("API_TOKEN", raising=False)
    with pytest.raises(ValueError, match="API_TOKEN"):
        Settings.from_env()


def test_secret_is_not_in_settings_repr():
    assert TOKEN not in repr(Settings(api_token=TOKEN))
