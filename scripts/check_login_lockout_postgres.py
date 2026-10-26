"""Local database probe; creates/removes one synthetic user, preserving audit records."""
import hashlib
import json
import os
import secrets
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from threading import Barrier

from fastapi import HTTPException
from sqlalchemy import delete, select
from app.auth import Auth
from app.config import Settings
from app.db import schema as db
from app.db.store import Store

store = Store(os.environ['DATABASE_URL'])
assert store.engine.dialect.name == 'postgresql'
username = 'lockout-probe-' + uuid.uuid4().hex
user_id = uuid.uuid4().hex
password = secrets.token_urlsafe(32)
key = hashlib.sha256(username.encode()).hexdigest()
settings = Settings(jwt_secret=secrets.token_urlsafe(48), demo_password=password, admin_password=secrets.token_urlsafe(32))
auths = [Auth(settings, store) for _ in range(8)]
barrier = Barrier(8)
class SynchronizedHasher:
    def __init__(self, delegate):
        self.delegate = delegate
    def verify(self, hashed, supplied):
        barrier.wait(timeout=10)
        return self.delegate.verify(hashed, supplied)
try:
    with store.transaction() as connection:
        assert connection.scalar(select(db.roles.c.id).where(db.roles.c.id == 'viewer'))
        connection.execute(db.users.insert().values(id=user_id, email=username,
            password_hash=auths[0].hasher.hash(password), role_id='viewer', disabled=False))
    for auth in auths:
        auth.initialized = True
        auth.hasher = SynchronizedHasher(auth.hasher)
    def fail(auth):
        try:
            auth.login(username, 'incorrect')
        except HTTPException as error:
            return error.status_code
        raise AssertionError('Incorrect password accepted')
    with ThreadPoolExecutor(max_workers=8) as executor:
        assert list(executor.map(fail, auths)) == [401] * 8
    with store.transaction() as connection:
        attempt = dict(connection.execute(select(db.login_attempts).where(db.login_attempts.c.id == key)).mappings().one())
    assert attempt['failures'] == 5
    fresh = Auth(settings, store)
    fresh.initialized = True
    try:
        fresh.login(username, password)
    except HTTPException as error:
        assert error.status_code == 401
    else:
        raise AssertionError('Active lock bypassed')
    with store.transaction() as connection:
        assert dict(connection.execute(select(db.login_attempts).where(db.login_attempts.c.id == key)).mappings().one()) == attempt
    print(json.dumps({'measured_at':datetime.now(timezone.utc).isoformat(),
        'environment':'local Docker PostgreSQL','concurrent_attempts':8,
        'rejected_attempts':8,'lock_threshold':5,'correct_password_rejected_during_lock':True,
        'locked_requests_do_not_extend_lock':True,'status':'passed'}))
finally:
    with store.transaction() as connection:
        connection.execute(delete(db.login_attempts).where(db.login_attempts.c.id == key))
        connection.execute(delete(db.users).where(db.users.c.id == user_id))
    store.engine.dispose()
