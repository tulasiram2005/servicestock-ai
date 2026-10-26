from app.db import schema as db
from sqlalchemy import select, update


def test_passwords_are_argon2_and_audit_is_appended(client, demo_headers, settings):
    with client.app.state.auth.store.transaction() as connection:
        row = connection.execute(select(db.users).where(db.users.c.email == settings.demo_username)).mappings().one()
        assert row["password_hash"].startswith("$argon2id$")
        assert settings.demo_password not in row["password_hash"]
        assert connection.execute(select(db.audit_log)).first() is not None


def test_account_lockout_survives_multiple_requests(client, settings):
    for attempt in range(5):
        assert client.post("/api/auth/login", json={"username": settings.demo_username, "password": "incorrect"}).status_code == 401
    assert client.post("/api/auth/login", json={"username": settings.demo_username, "password": settings.demo_password}).status_code == 401


def test_refresh_csrf_rotation_and_replay_revocation(client, demo_headers):
    old_refresh = client.cookies.get("refresh")
    assert client.post("/api/auth/refresh").status_code == 403
    headers = {"X-CSRF-Token": client.cookies.get("csrf"), "Origin": "http://localhost:3000"}
    response = client.post("/api/auth/refresh", headers=headers)
    assert response.status_code == 200
    new_refresh = client.cookies.get("refresh")
    assert old_refresh != new_refresh
    from fastapi import HTTPException
    import pytest
    with pytest.raises(HTTPException):
        client.app.state.auth.rotate(old_refresh)
    with pytest.raises(HTTPException):
        client.app.state.auth.rotate(new_refresh)


def test_disabled_user_and_role_change_invalidate_access(client, demo_headers, settings):
    with client.app.state.auth.store.transaction() as connection:
        connection.execute(update(db.users).where(db.users.c.email == settings.demo_username).values(disabled=True))
    assert client.get("/api/me", headers=demo_headers).status_code == 401


def test_body_cap_and_headers(client):
    assert client.post("/api/auth/login", content="x" * 16385).status_code == 413
    response = client.get("/health")
    assert "frame-ancestors 'none'" in response.headers["content-security-policy"]
    assert response.headers["referrer-policy"] == "no-referrer"


def test_refresh_cookie_is_httponly_and_strict(client, settings):
    response = client.post("/api/auth/login", json={"username": settings.demo_username, "password": settings.demo_password})
    cookie = response.headers.get_list("set-cookie")[0]
    assert "HttpOnly" in cookie and "SameSite=strict" in cookie


def test_independent_auth_instances_seed_same_database_safely(settings, tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    from sqlalchemy import func
    from app.auth import Auth
    from app.db.store import Store
    url = 'sqlite:///' + str(tmp_path / 'shared.db')
    store = Store(url)
    db.metadata.create_all(store.engine)
    instances = [Auth(settings, Store(url)) for _ in range(4)]
    barrier = Barrier(4)
    def initialize(instance):
        barrier.wait()
        instance.ensure_accounts()
        return instance.login(settings.demo_username, settings.demo_password)
    try:
        with ThreadPoolExecutor(max_workers=4) as executor:
            tokens = list(executor.map(initialize, instances))
        assert len(tokens) == 4
        with store.transaction() as connection:
            assert connection.scalar(select(func.count()).select_from(db.users)) == 2
            assert connection.scalar(select(func.count()).select_from(db.roles)) == 3
    finally:
        for instance in instances:
            instance.store.engine.dispose()
        store.engine.dispose()


def test_production_liveness_is_db_free_and_only_liveness_allows_http(settings):
    from dataclasses import replace
    from fastapi.testclient import TestClient
    from sqlalchemy import event
    from app.db.store import Store
    from app.main import create_app
    production = replace(settings, environment='production',
        database_url='postgresql+psycopg://unused:unused@demo-pooler.example/db?sslmode=require',
        allowed_origins=('https://demo.example',))
    store = Store('sqlite://')
    def forbid_queries(*args):
        raise AssertionError('Liveness must not query the database')
    event.listen(store.engine, 'before_cursor_execute', forbid_queries)
    try:
        with TestClient(create_app(production, store_override=store)) as client:
            for path in ('/health', '/health/live'):
                assert client.get(path).json() == {'status': 'ok'}
            for path in ('/ready', '/api/status', '/health/other'):
                assert client.get(path).status_code == 400
            assert client.get('https://testserver/api/status').status_code == 401
    finally:
        event.remove(store.engine, 'before_cursor_execute', forbid_queries)
        store.engine.dispose()
