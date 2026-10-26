import asyncio
from dataclasses import replace
import time

import pytest
from fastapi import HTTPException
from sqlalchemy import select, update

from app.db import schema as db
from app.db.store import Store
from app.jobs import JobQueue, Worker
from app.services import retain


@pytest.fixture
def queue(settings):
    store = Store("sqlite://")
    db.metadata.create_all(store.engine)
    return JobQueue(store, replace(settings, job_lease_seconds=1, job_max_attempts=2))


def test_idempotency_conflict_and_ownership(queue):
    first = queue.enqueue("alice", "whatif", {"part": "P1"}, "same-key")
    assert queue.enqueue("alice", "whatif", {"part": "P1"}, "same-key")["id"] == first["id"]
    assert queue.enqueue("bob", "whatif", {"part": "P1"}, "same-key")["id"] != first["id"]
    with pytest.raises(HTTPException) as error:
        queue.enqueue("alice", "whatif", {"part": "P2"}, "same-key")
    assert error.value.status_code == 409


def test_expired_lease_is_reclaimed_and_old_worker_is_fenced(queue):
    queue.enqueue("alice", "whatif", {}, "same-key")
    first = queue.claim()
    with queue.store.transaction() as connection:
        connection.execute(update(db.jobs).where(db.jobs.c.id == first["id"]).values(lease_until=time.time() - 1))
    second = queue.claim()
    assert second["attempts"] == 2
    assert not queue.finish(first, {"stale": True})
    assert queue.finish(second, {"fresh": True})


def test_retry_backoff_and_dead_letter(queue):
    queue.enqueue("alice", "whatif", {}, "same-key")
    first = queue.claim()
    assert queue.finish(first, failed=True)
    assert queue.claim() is None
    with queue.store.transaction() as connection:
        connection.execute(update(db.jobs).values(available_at=time.time() - 1))
    second = queue.claim()
    queue.finish(second, failed=True)
    with queue.store.transaction() as connection:
        assert connection.scalar(select(db.jobs.c.status)) == "dead"


def test_idle_worker_never_polls():
    class FakeQueue:
        calls = 0
        def claim(self):
            self.calls += 1
            return None
        def next_due(self):
            return None
    async def exercise():
        fake = FakeQueue()
        worker = Worker(fake, lambda kind, payload: {})
        task = asyncio.create_task(worker.run())
        await asyncio.sleep(0.05)
        assert fake.calls == 1
        await asyncio.sleep(0.1)
        assert fake.calls == 1
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
    asyncio.run(exercise())


def test_retention_preserves_active_jobs(queue):
    queue.enqueue("alice", "whatif", {}, "same-key")
    with queue.store.transaction() as connection:
        connection.execute(db.audit_log.insert().values(id="old", actor="a", action="login", detail={}, created_at=1))
    result = retain(queue.store, 30)
    assert result["deleted"]["audit_log"] == 1
    with queue.store.transaction() as connection:
        assert connection.scalar(select(db.jobs.c.id))
