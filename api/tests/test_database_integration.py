import os
from concurrent.futures import ThreadPoolExecutor
import uuid

import pytest
from sqlalchemy import select, delete

from app.db.store import Store
from app.db import schema as db
from app.jobs import JobQueue


@pytest.mark.skipif(not os.getenv("TEST_DATABASE_URL"), reason="Dedicated integration database URL not configured")
def test_database_job_claims_are_exclusive(settings):
    store = Store(os.environ["TEST_DATABASE_URL"])
    db.metadata.create_all(store.engine)
    queue = JobQueue(store, settings)
    owner = "integration-" + uuid.uuid4().hex
    identifiers = [queue.enqueue(owner, "whatif", {}, uuid.uuid4().hex)["id"] for index in range(10)]
    try:
        with ThreadPoolExecutor(max_workers=4) as pool:
            claimed = list(pool.map(lambda _: queue.claim(), range(10)))
        assert len({job["id"] for job in claimed if job}) == 10
        assert all(queue.finish(job, {"status": "tested"}) for job in claimed)
    finally:
        with store.transaction() as connection:
            connection.execute(delete(db.jobs).where(db.jobs.c.owner == owner))


@pytest.mark.skipif(not os.getenv('TEST_DATABASE_URL'), reason='Dedicated integration database URL not configured')
def test_database_model_budget_is_atomic(settings):
    from app.llm_budget import DatabaseBudget
    import secrets
    store = Store(os.environ['TEST_DATABASE_URL'])
    db.metadata.create_all(store.engine)
    day = -1000000000 - secrets.randbelow(100000000)
    try:
        with ThreadPoolExecutor(max_workers=4) as executor:
            accepted = sum(executor.map(lambda index: DatabaseBudget(store).reserve('quota-probe-'+str(index),day,5,1),range(12)))
        assert accepted == 5
        assert DatabaseBudget(store).total(day) == 5
    finally:
        with store.transaction() as connection:
            connection.execute(delete(db.llm_daily_usage).where(db.llm_daily_usage.c.day == day))
        store.engine.dispose()


@pytest.mark.parametrize('backend', ['sqlite', 'configured'])
def test_refresh_token_can_only_be_rotated_once_concurrently(settings, tmp_path, backend):
    from dataclasses import replace
    from threading import Barrier
    from fastapi import HTTPException
    from app.auth import Auth
    if backend == 'configured' and not os.getenv('TEST_DATABASE_URL'):
        pytest.skip('Dedicated integration database URL not configured')
    url = (os.environ['TEST_DATABASE_URL'] if backend == 'configured'
           else 'sqlite:///' + str(tmp_path / 'refresh-concurrency.db'))
    suffix = uuid.uuid4().hex
    isolated = replace(settings, demo_username='refresh-viewer-'+suffix,
                       admin_username='refresh-admin-'+suffix)
    stores = [Store(url) for _ in range(4)]
    db.metadata.create_all(stores[0].engine)
    instances = [Auth(isolated, store) for store in stores]
    for instance in instances:
        instance.ensure_accounts()
    original = instances[0].create_refresh(isolated.demo_username)
    barrier = Barrier(len(instances))
    def rotate(instance):
        barrier.wait(timeout=10)
        try:
            return instance.rotate(original)
        except HTTPException as error:
            assert error.status_code == 401
            return None
    try:
        with ThreadPoolExecutor(max_workers=4) as executor:
            results = list(executor.map(rotate, instances))
        winners = [result for result in results if result is not None]
        assert len(winners) == 1
        # Replay revokes the entire family, including the winner's replacement.
        with pytest.raises(HTTPException) as error:
            instances[0].rotate(winners[0][1])
        assert error.value.status_code == 401
        with stores[0].transaction() as connection:
            rows = connection.execute(select(db.refresh_tokens).where(
                db.refresh_tokens.c.username == isolated.demo_username)).mappings().all()
            assert len(rows) == 2
            assert all(row['revoked'] for row in rows)
    finally:
        with stores[0].transaction() as connection:
            connection.execute(delete(db.refresh_tokens).where(db.refresh_tokens.c.username == isolated.demo_username))
            connection.execute(delete(db.users).where(db.users.c.email.in_(
                [isolated.demo_username, isolated.admin_username])))
        for store in stores:
            store.engine.dispose()
