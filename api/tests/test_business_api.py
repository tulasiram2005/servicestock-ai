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


def test_user_access_changes_are_authorized_audited_and_revoke_tokens(settings):
    from argon2 import PasswordHasher
    store = Store("sqlite://")
    db.metadata.create_all(store.engine)
    seed(store)
    with TestClient(create_app(settings, store_override=store)) as client:
        admin_token = client.post('/api/auth/login', json={"username":"admin", "password":settings.admin_password}).json()["access_token"]
        admin_headers = {"Authorization":"Bearer " + admin_token}
        with store.transaction() as connection:
            connection.execute(db.users.insert().values(id="editable", email="planner-test", role_id="viewer",
                password_hash=PasswordHasher().hash("test-planner-password"), disabled=False))
        token = client.post('/api/auth/login', json={"username":"planner-test", "password":"test-planner-password"}).json()["access_token"]
        viewer_headers = {"Authorization":"Bearer " + token}
        body = {"role":"planner", "disabled":False}
        assert client.post('/api/admin/users/editable', json=body, headers=viewer_headers).status_code == 403
        assert client.post('/api/admin/users/editable', json=body, headers=admin_headers).status_code == 200
        assert client.get('/api/me', headers=viewer_headers).status_code == 401
        accounts = client.get('/api/admin/users', headers=admin_headers).json()
        managed = next(user for user in accounts if user['email'] == 'admin')
        assert managed['managed']
        assert client.post('/api/admin/users/'+managed['id'], json=body, headers=admin_headers).status_code == 403
        assert client.post('/api/admin/users/editable', json={"role":"planner", "disabled":True}, headers=admin_headers).status_code == 200
        assert client.post('/api/auth/login', json={"username":"planner-test", "password":"test-planner-password"}).status_code == 401
        with store.transaction() as connection:
            audits = connection.execute(select(db.audit_log).where(db.audit_log.c.action == 'change_role')).mappings().all()
        assert len(audits) == 2
        assert audits[0]['detail']['previous_role'] == 'viewer'
        from sqlalchemy import event
        def reject_audit(connection, cursor, statement, parameters, context, executemany):
            if statement.startswith('INSERT INTO audit_log'):
                raise RuntimeError('Simulated audit storage failure')
        event.listen(store.engine, 'before_cursor_execute', reject_audit)
        try:
            with pytest.raises(RuntimeError, match='audit storage failure'):
                client.post('/api/admin/users/editable', json={"role":"admin", "disabled":False}, headers=admin_headers)
        finally:
            event.remove(store.engine, 'before_cursor_execute', reject_audit)
        with store.transaction() as connection:
            unchanged = connection.execute(select(db.users).where(db.users.c.id == 'editable')).mappings().one()
        assert unchanged['role_id'] == 'planner'
        assert unchanged['disabled'] is True


def test_part_sensitivity_holds_other_policy_inputs_fixed():
    from app.services import part_detail
    store=Store('sqlite://')
    db.metadata.create_all(store.engine)
    seed(store)
    publish(store,Path(__file__).resolve().parents[2]/'results')
    try:
        detail=part_detail(store,'P0001')
        policy=detail['policy']
        expected=sorted([cell for cell in artifact(store,'analytics')['grid'] if cell['part_id']=='P0001'
            and cell['target_service_level']==policy['target_service_level']
            and cell['holding_rate']==policy['holding_rate']],key=lambda c:c['lead_time_multiplier'])
        assert [p['lead_time_multiplier'] for p in detail['lead_sensitivity']]==[0.5,1.0,2.0]
        assert [p['annual_cost'] for p in detail['lead_sensitivity']]==[p['optimized']['expected_annual_cost'] for p in expected]
        assert sum(policy['histogram']['counts'])==policy['draws']
    finally:
        store.engine.dispose()


def test_quality_history_is_bounded_chronological_and_counts_are_honest(settings):
    store=Store('sqlite://')
    db.metadata.create_all(store.engine)
    seed(store)
    payload={'quality_score':50,'rows_received':2,'rows_accepted':1,'quarantined':1,
             'issues':[{'rule':'validity','quarantined':True},{'rule':'outlier','quarantined':False}]}
    with store.transaction() as connection:
        connection.execute(db.artifacts['dq_runs'].delete())
        for index in range(35):
            connection.execute(db.artifacts['dq_runs'].insert().values(id=f'run-{index:02}',run_id=f'run-{index:02}',created_at=index,payload=payload))
    try:
        with TestClient(create_app(settings,store_override=store)) as client:
            assert client.get('/api/dq').status_code==401
            token=client.post('/api/auth/login',json={'username':'demo','password':settings.demo_password}).json()['access_token']
            result=client.get('/api/dq',headers={'Authorization':'Bearer '+token}).json()
            assert [run['created_at'] for run in result['history']]==list(range(5,35))
            rules={row['rule']:row for row in result['rule_results']}
            assert rules['validity']['quarantined']==1
            assert rules['outlier']['flagged']==1
            assert rules['outlier']['quarantined']==0
            assert rules['completeness']['flagged']==0
            assert result['quality_score']==50
    finally:
        store.engine.dispose()


def test_quality_without_runs_is_explicitly_unmeasured(settings):
    store=Store('sqlite://')
    db.metadata.create_all(store.engine)
    try:
        with TestClient(create_app(settings,store_override=store)) as client:
            token=client.post('/api/auth/login',json={'username':'demo','password':settings.demo_password}).json()['access_token']
            report=client.get('/api/dq',headers={'Authorization':'Bearer '+token}).json()
            assert report=={'issues':[],'history':[],'rule_results':[],'quality_score':None}
    finally:
        store.engine.dispose()
