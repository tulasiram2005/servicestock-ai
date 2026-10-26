from contextlib import contextmanager
import time
import uuid

from sqlalchemy import create_engine, event, text
from sqlalchemy.pool import NullPool, StaticPool

from .schema import audit_log


class Store:
    def __init__(self, url, timeout_ms=5000):
        kwargs = {"poolclass": NullPool}
        if url.startswith("sqlite"):
            kwargs = {"connect_args": {"check_same_thread": False}, "poolclass": StaticPool}
        elif url.startswith("postgresql"):
            kwargs["connect_args"] = {"connect_timeout": 5}
        self.engine = create_engine(url, hide_parameters=True, **kwargs)
        self.timeout_ms = timeout_ms
        if self.engine.dialect.name == "sqlite":
            @event.listens_for(self.engine, "connect")
            def enable_foreign_keys(connection, record):
                connection.execute("PRAGMA foreign_keys=ON")

    @contextmanager
    def transaction(self):
        with self.engine.begin() as connection:
            if self.engine.dialect.name == "postgresql":
                connection.execute(text("SELECT set_config('statement_timeout', :value, true)"), {"value": str(self.timeout_ms)})
                connection.execute(text("SELECT set_config('lock_timeout', :value, true)"), {"value": str(self.timeout_ms)})
            yield connection

    def audit(self, actor, action, detail):
        with self.transaction() as connection:
            connection.execute(audit_log.insert().values(id=uuid.uuid4().hex, actor=actor, action=action,
                                                        detail=detail, created_at=time.time()))
