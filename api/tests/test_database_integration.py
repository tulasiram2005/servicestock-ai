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
