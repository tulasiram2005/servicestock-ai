import asyncio
from .config import Settings
from .db.store import Store
from .jobs import JobQueue, Worker
from .services import handle_job

if __name__ == "__main__":
    settings = Settings.from_env()
    store = Store(settings.database_url, settings.statement_timeout_ms)
    worker = Worker(JobQueue(store, settings), lambda kind, payload: handle_job(store, settings, kind, payload))
    asyncio.run(worker.run(standalone=True))
