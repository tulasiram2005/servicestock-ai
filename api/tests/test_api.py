from dataclasses import replace
import time

import jwt
import pytest

from app.config import Settings
from app.runtime import MemoryRateLimiter, TTLCache


def test_health_has_no_secrets_or_database_dependency(client):
    for path in ("/health", "/health/live"):
        response = client.get(path)
        assert response.json() == {"status": "ok"}
        assert response.headers["cache-control"] == "no-store"


@pytest.mark.parametrize("headers", [{}, {"Authorization": "Bearer wrong"}])
def test_private_routes_require_valid_token(client, headers):
    assert client.get("/api/status", headers=headers).status_code == 401
    assert client.post("/api/assistant", json={"text": "hello"}, headers=headers).status_code == 401


def test_status_is_honest_and_supports_conditional_requests(client, demo_headers, settings):
    response = client.get("/api/status", headers=demo_headers)
    assert response.status_code == 200
    assert response.json()["metrics"] is None
    assert response.json()["database_connected"] is False
    assert settings.jwt_secret not in response.text
    cached = client.get("/api/status", headers={**demo_headers, "If-None-Match": response.headers["etag"]})
    assert cached.status_code == 304
    assert client.get("/api/status", headers={"If-None-Match": response.headers["etag"]}).status_code == 401


def test_mock_is_explicit_and_does_not_echo_input(client, demo_headers):
    response = client.post("/api/assistant", json={"text": "private customer data"}, headers=demo_headers)
    assert response.status_code == 200
    assert response.json()["is_mock"] is True
    assert "private customer data" not in response.text


@pytest.mark.parametrize("body", [{"text": ""}, {"text": "x" * 4001}, {"text": "hello", "role": "admin"}])
def test_prompt_bounds(client, demo_headers, body):
    assert client.post("/api/assistant", json=body, headers=demo_headers).status_code == 422


def test_rate_limit_recovers_after_window_and_is_bounded():
    current = [0]
    limiter = MemoryRateLimiter(limit=2, clock=lambda: current[0], max_keys=1)
    assert limiter.allow("alice")
    assert limiter.allow("alice")
    assert not limiter.allow("alice")
    assert not limiter.allow("bob")
    current[0] = 60
    assert limiter.allow("bob")


def test_http_rate_limit(client, demo_headers, settings):
    for attempt in range(settings.rate_limit):
        assert client.get("/api/status", headers=demo_headers).status_code == 200
    assert client.get("/api/status", headers=demo_headers).status_code == 429


def test_missing_secret_fails_closed(monkeypatch):
    monkeypatch.delenv("JWT_SECRET", raising=False)
    with pytest.raises(ValueError, match="JWT_SECRET"):
        Settings.from_env()


def test_secret_is_not_in_settings_repr(settings):
    for secret in (settings.jwt_secret, settings.admin_password, settings.demo_password):
        assert secret not in repr(settings)


def test_demo_cannot_read_admin_metrics(client, demo_headers, admin_headers):
    assert client.get("/api/me", headers=demo_headers).json()["role"] == "demo"
    assert client.get("/metrics", headers=demo_headers).status_code == 403
    response = client.get("/metrics", headers=admin_headers)
    assert response.status_code == 200
    assert response.json()["requests"] > 0
    assert response.json()["scope"] == "current_process"


@pytest.mark.parametrize("username", ["demo", "unknown"])
def test_wrong_credentials_are_generic(client, username):
    response = client.post("/api/auth/login", json={"username": username, "password": "wrong"})
    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid credentials"}


@pytest.mark.parametrize("change", [{"exp": 1}, {"aud": "other"}, {"role": "admin"}, {"sub": "unknown"}])
def test_jwt_claims_are_enforced(client, settings, change):
    claims = {"sub": "demo", "role": "demo", "iat": int(time.time()), "nbf": int(time.time()),
              "exp": int(time.time()) + 60, "iss": "servicestock", "aud": "servicestock-api", **change}
    token = jwt.encode(claims, settings.jwt_secret, algorithm="HS256")
    assert client.get("/api/me", headers={"Authorization": "Bearer " + token}).status_code == 401


def test_ttl_cache_expires_and_evicts():
    current = [0]
    cache = TTLCache(capacity=1, ttl=10, clock=lambda: current[0])
    cache.put("a", 1)
    cache.put("b", 2)
    assert cache.get("a") is None
    assert cache.get("b") == 2
    current[0] = 10
    assert cache.get("b") is None


def test_production_configuration_fails_closed(settings):
    with pytest.raises(ValueError, match="pooled PostgreSQL"):
        replace(settings, environment="production")
    with pytest.raises(ValueError, match="disable uploads"):
        replace(settings, environment="production", uploads_enabled=True)
    with pytest.raises(ValueError, match="distinct"):
        replace(settings, admin_password=settings.demo_password)


def test_cors_uses_exact_allowlist(client):
    assert "access-control-allow-origin" not in client.get("/health", headers={"Origin": "https://evil.example"}).headers
    assert client.get("/health", headers={"Origin": "http://localhost:3000"}).headers["access-control-allow-origin"] == "http://localhost:3000"
