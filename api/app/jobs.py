import asyncio
import contextlib
import json
import time
import uuid

from sqlalchemy import select, update, func, or_, text
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException

from .db import schema as db


class JobQueue:
    def __init__(self, store, settings):
        self.store, self.settings = store, settings

    def enqueue(self, owner, kind, payload, key):
        if len(json.dumps(payload)) > 8192:
            raise HTTPException(413, "Job payload too large")
        try:
            with self.store.transaction() as connection:
                existing = connection.execute(select(db.jobs).where(db.jobs.c.owner == owner, db.jobs.c.idempotency_key == key)).mappings().first()
                if existing:
                    if existing["kind"] != kind or existing["payload"] != payload:
                        raise HTTPException(409, "Idempotency key has different input")
                    return dict(existing)
                if self.store.engine.dialect.name == "postgresql":
                    size = connection.scalar(text("SELECT pg_database_size(current_database())"))
                    if size >= self.settings.db_target_bytes and kind != "retention":
                        raise HTTPException(507, "Storage budget reached; run retention before enqueueing")
                count = connection.scalar(select(func.count()).select_from(db.jobs).where(db.jobs.c.status.in_(["pending", "running"])))
                if count >= self.settings.jobs_max_pending:
                    raise HTTPException(429, "Job queue is full")
                now = time.time()
                record = {"id": uuid.uuid4().hex, "owner": owner, "kind": kind, "payload": payload,
                          "idempotency_key": key, "status": "pending", "progress": 0, "attempts": 0,
                          "available_at": now, "created_at": now, "updated_at": now}
                connection.execute(db.jobs.insert().values(**record))
                return record
        except IntegrityError:
            with self.store.transaction() as connection:
                existing = connection.execute(select(db.jobs).where(db.jobs.c.owner == owner, db.jobs.c.idempotency_key == key)).mappings().first()
                if not existing:
                    raise
                if existing["kind"] != kind or existing["payload"] != payload:
                    raise HTTPException(409, "Idempotency key has different input") from None
                return dict(existing)

    def claim(self, now=None):
        now = time.time() if now is None else now
        with self.store.transaction() as connection:
            connection.execute(update(db.jobs).where(db.jobs.c.status == "running", db.jobs.c.lease_until <= now,
                db.jobs.c.attempts >= self.settings.job_max_attempts).values(status="dead", error="lease_expired", updated_at=now))
            query = select(db.jobs).where(or_(
                (db.jobs.c.status == "pending") & (db.jobs.c.available_at <= now),
                (db.jobs.c.status == "running") & (db.jobs.c.lease_until <= now)),
                db.jobs.c.attempts < self.settings.job_max_attempts).order_by(db.jobs.c.created_at, db.jobs.c.id).limit(1)
            if self.store.engine.dialect.name == "mssql":
                query = query.with_hint(db.jobs, "WITH (UPDLOCK, READPAST, ROWLOCK)", dialect_name="mssql")
            else:
                query = query.with_for_update(skip_locked=True)
            job = connection.execute(query).mappings().first()
            if not job:
                return None
            token = uuid.uuid4().hex
            connection.execute(update(db.jobs).where(db.jobs.c.id == job["id"]).values(
                status="running", attempts=job["attempts"] + 1, lease_until=now + self.settings.job_lease_seconds,
                lease_token=token, progress=5, updated_at=now))
            return {**job, "lease_token": token, "attempts": job["attempts"] + 1}

    def heartbeat(self, job, progress=50):
        with self.store.transaction() as connection:
            changed = connection.execute(update(db.jobs).where(db.jobs.c.id == job["id"], db.jobs.c.lease_token == job["lease_token"],
                db.jobs.c.status == "running", db.jobs.c.lease_until > time.time()).values(
                lease_until=time.time() + self.settings.job_lease_seconds, progress=progress, updated_at=time.time()))
            return changed.rowcount == 1

    def finish(self, job, result=None, failed=False):
        if result is not None and len(json.dumps(result)) > 128000:
            failed, result = True, None
        with self.store.transaction() as connection:
            status = ("dead" if job["attempts"] >= self.settings.job_max_attempts else "pending") if failed else "succeeded"
            changed = connection.execute(update(db.jobs).where(db.jobs.c.id == job["id"], db.jobs.c.lease_token == job["lease_token"],
                db.jobs.c.status == "running", db.jobs.c.lease_until > time.time()).values(status=status,
                result=result, error="execution_failed" if failed else None, progress=0 if failed else 100,
                available_at=time.time() + self.settings.job_retry_seconds * 2 ** (job["attempts"] - 1),
                lease_until=None, lease_token=None, updated_at=time.time()))
            return changed.rowcount == 1

    def next_due(self):
        with self.store.transaction() as connection:
            pending = connection.scalar(select(func.min(db.jobs.c.available_at)).where(db.jobs.c.status == "pending"))
            running = connection.scalar(select(func.min(db.jobs.c.lease_until)).where(db.jobs.c.status == "running"))
            values = [value for value in (pending, running) if value is not None]
            return max(0.05, min(values) - time.time()) if values else None


class Worker:
    def __init__(self, queue, handler):
        self.queue, self.handler = queue, handler
        self.event = asyncio.Event()

    def wake(self):
        self.event.set()

    async def drain(self):
        while True:
            job = await asyncio.to_thread(self.queue.claim)
            if job is None:
                return await asyncio.to_thread(self.queue.next_due)
            async def heartbeat():
                while True:
                    await asyncio.sleep(max(0.1, self.queue.settings.job_lease_seconds / 3))
                    if not await asyncio.to_thread(self.queue.heartbeat, job):
                        return
            beat = asyncio.create_task(heartbeat())
            try:
                result = await asyncio.to_thread(self.handler, job["kind"], job["payload"])
                await asyncio.to_thread(self.queue.finish, job, result)
            except Exception:
                await asyncio.to_thread(self.queue.finish, job, None, True)
            finally:
                beat.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await beat

    async def run(self, standalone=False):
        self.wake()
        while True:
            await self.event.wait()
            self.event.clear()
            try:
                delay = await self.drain()
            except Exception:
                if standalone:
                    raise
                continue
            if delay is None:
                if standalone:
                    return
                continue
            try:
                await asyncio.wait_for(self.event.wait(), timeout=delay)
            except asyncio.TimeoutError:
                self.wake()
