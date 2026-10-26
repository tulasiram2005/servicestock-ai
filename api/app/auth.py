import hashlib
import secrets
import time
import uuid
from dataclasses import dataclass
from threading import Lock

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerificationError
from fastapi import HTTPException
from sqlalchemy import select, update

from .db import schema as db
from .db.store import Store


@dataclass(frozen=True)
class Principal:
    username: str
    role: str


class Auth:
    def __init__(self, settings, store=None):
        self.settings = settings
        self.store = store or Store("sqlite://")
        if store is None:
            db.metadata.create_all(self.store.engine)
        self.hasher = PasswordHasher(time_cost=2, memory_cost=19456, parallelism=1)
        self.dummy = self.hasher.hash(secrets.token_urlsafe(32))
        self.initialized = False
        self.lock = Lock()

    def ensure_accounts(self):
        with self.lock:
            if self.initialized:
                return
            with self.store.transaction() as connection:
                for role in ("viewer", "planner", "admin"):
                    if not connection.scalar(select(db.roles.c.id).where(db.roles.c.id == role)):
                        connection.execute(db.roles.insert().values(id=role, name=role))
                for username, password, role in ((self.settings.demo_username, self.settings.demo_password, "viewer"),
                                                   (self.settings.admin_username, self.settings.admin_password, "admin")):
                    if not connection.scalar(select(db.users.c.id).where(db.users.c.email == username)):
                        connection.execute(db.users.insert().values(id=uuid.uuid4().hex, email=username,
                            password_hash=self.hasher.hash(password), role_id=role, disabled=False))
            self.initialized = True

    def issue_access(self, username, role):
        now = int(time.time())
        return jwt.encode({"sub": username, "role": role, "iat": now, "nbf": now,
                           "exp": now + self.settings.token_minutes * 60,
                           "iss": "servicestock", "aud": "servicestock-api"},
                          self.settings.jwt_secret, algorithm="HS256")

    def login(self, username, password):
        self.ensure_accounts()
        key = hashlib.sha256(username.encode()).hexdigest()
        with self.store.transaction() as connection:
            account = connection.execute(select(db.users).where(db.users.c.email == username)).mappings().first()
            attempt = connection.execute(select(db.login_attempts).where(db.login_attempts.c.id == key)).mappings().first()
        try:
            valid = self.hasher.verify(account["password_hash"] if account else self.dummy, password)
        except VerificationError:
            valid = False
        locked = bool(attempt and attempt["locked_until"] > time.time())
        if not valid or not account or account["disabled"] or locked:
            if account:
                failures = (attempt["failures"] if attempt else 0) + 1
                with self.store.transaction() as connection:
                    values = {"failures": failures, "locked_until": time.time() + 300 if failures >= 5 else 0}
                    if attempt:
                        connection.execute(update(db.login_attempts).where(db.login_attempts.c.id == key).values(**values))
                    else:
                        connection.execute(db.login_attempts.insert().values(id=key, **values))
            self.store.audit("redacted", "login_failed", {})
            raise HTTPException(401, "Invalid credentials")
        with self.store.transaction() as connection:
            connection.execute(db.login_attempts.delete().where(db.login_attempts.c.id == key))
        self.store.audit(account["id"], "login", {})
        return self.issue_access(username, account["role_id"])

    def authenticate(self, token):
        try:
            payload = jwt.decode(token, self.settings.jwt_secret, algorithms=["HS256"],
                issuer="servicestock", audience="servicestock-api",
                options={"require": ["sub", "role", "iat", "nbf", "exp", "iss", "aud"]})
            self.ensure_accounts()
            with self.store.transaction() as connection:
                account = connection.execute(select(db.users).where(db.users.c.email == payload["sub"])).mappings().first()
            if not account or account["disabled"] or payload["role"] != account["role_id"]:
                raise ValueError()
            return Principal(payload["sub"], account["role_id"])
        except (jwt.InvalidTokenError, ValueError, TypeError):
            raise HTTPException(401, "Authentication required", headers={"WWW-Authenticate": "Bearer"}) from None

    def create_refresh(self, username, family=None):
        token = secrets.token_urlsafe(48)
        with self.store.transaction() as connection:
            connection.execute(db.refresh_tokens.insert().values(id=hashlib.sha256(token.encode()).hexdigest(),
                family=family or uuid.uuid4().hex, username=username, expires_at=time.time() + 7 * 86400,
                used=False, revoked=False))
        return token

    def rotate(self, token):
        hashed = hashlib.sha256(token.encode()).hexdigest()
        invalid = False
        with self.store.transaction() as connection:
            row = connection.execute(select(db.refresh_tokens).where(db.refresh_tokens.c.id == hashed).with_for_update()).mappings().first()
            if not row or row["expires_at"] <= time.time() or row["revoked"] or row["used"]:
                if row:
                    connection.execute(update(db.refresh_tokens).where(db.refresh_tokens.c.family == row["family"]).values(revoked=True))
                invalid = True
            else:
                connection.execute(update(db.refresh_tokens).where(db.refresh_tokens.c.id == hashed).values(used=True))
                account = connection.execute(select(db.users).where(db.users.c.email == row["username"])).mappings().first()
                if not account or account["disabled"]:
                    invalid = True
                else:
                    replacement = secrets.token_urlsafe(48)
                    connection.execute(db.refresh_tokens.insert().values(id=hashlib.sha256(replacement.encode()).hexdigest(),
                        family=row["family"], username=row["username"], expires_at=time.time() + 604800,
                        used=False, revoked=False))
        if invalid:
            raise HTTPException(401, "Session expired; sign in again")
        return self.issue_access(row["username"], account["role_id"]), replacement

    def logout(self, token):
        with self.store.transaction() as connection:
            row = connection.execute(select(db.refresh_tokens).where(db.refresh_tokens.c.id == hashlib.sha256(token.encode()).hexdigest())).mappings().first()
            if row:
                connection.execute(update(db.refresh_tokens).where(db.refresh_tokens.c.family == row["family"]).values(revoked=True))
