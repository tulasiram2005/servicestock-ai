import os
import uuid
from concurrent.futures import ThreadPoolExecutor
from sqlalchemy import delete
from app.config import Settings
from app.db import schema as db
from app.db.store import Store
from app.jobs import JobQueue

settings = Settings.from_env()
store = Store(os.environ["DATABASE_URL"])
queue = JobQueue(store, settings)
owner = "concurrency-" + uuid.uuid4().hex
identifiers = [queue.enqueue(owner, "whatif", {}, uuid.uuid4().hex)["id"] for index in range(10)]
try:
    with ThreadPoolExecutor(max_workers=4) as executor:
        claimed = list(executor.map(lambda _: queue.claim(), range(10)))
    assert len({job["id"] for job in claimed if job}) == 10
    assert all(queue.finish(job, {"verified": True}) for job in claimed)
    print("PostgreSQL: 10 jobs claimed uniquely by 4 concurrent threads; all completions fenced successfully.")
finally:
    with store.transaction() as connection:
        connection.execute(delete(db.jobs).where(db.jobs.c.owner == owner))
