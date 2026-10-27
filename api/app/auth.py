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
from sqlalchemy.exc import IntegrityError

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
                def insert_missing(table, key, values):
                    if connection.scalar(select(table.c.id).where(key)):
                        return
                    try:
                        with connection.begin_nested():
                            connection.execute(table.insert().values(**values))
                    except IntegrityError:
                        # A competing process may have seeded this same identity.
                        # Keep the outer transaction usable and do not hide other errors.
                        if not connection.scalar(select(table.c.id).where(key)):
                            raise
                for role in ("viewer", "planner", "admin"):
                    insert_missing(db.roles, db.roles.c.id == role, {"id": role, "name": role})
                for username, password, role in ((self.settings.demo_username, self.settings.demo_password, "viewer"),
                                                   (self.settings.admin_username, self.settings.admin_password, "admin")):
                    if not connection.scalar(select(db.users.c.id).where(db.users.c.email == username)):
                        insert_missing(db.users, db.users.c.email == username, dict(id=uuid.uuid4().hex, email=username,
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
        try:
            valid = self.hasher.verify(account["password_hash"] if account else self.dummy, password)
        except VerificationError:
            valid = False
        accepted = False
        with self.store.transaction() as connection:
            # Serialize decisions for this account across processes. A no-op UPDATE
            # also locks on SQLite and SQL Server, which do not share FOR UPDATE syntax.
            if account:
                connection.execute(update(db.users).where(db.users.c.id == account["id"]).values(id=db.users.c.id))
                current = connection.execute(select(db.users).where(db.users.c.id == account["id"])).mappings().first()
            else:
                current = None
            now = time.time()
            attempt = connection.execute(select(db.login_attempts).where(db.login_attempts.c.id == key)).mappings().first()
            locked = bool(attempt and attempt["locked_until"] > now)
            accepted = bool(valid and current and not current["disabled"] and not locked
                            and current["password_hash"] == account["password_hash"])
            if accepted:
                connection.execute(db.login_attempts.delete().where(db.login_attempts.c.id == key))
            elif current and not locked:
                # An expired lock starts a fresh failure window; requests during a
                # lock do not extend it indefinitely or reset it with a valid password.
                previous = attempt["failures"] if attempt and not attempt["locked_until"] else 0
                failures = previous + 1
                values = {"failures": failures, "locked_until": now + 300 if failures >= 5 else 0}
                if attempt:
                    connection.execute(update(db.login_attempts).where(db.login_attempts.c.id == key).values(**values))
                else:
                    connection.execute(db.login_attempts.insert().values(id=key, **values))
            connection.execute(db.audit_log.insert().values(id=uuid.uuid4().hex,
                actor=current["id"] if accepted else "redacted",
                action="login" if accepted else "login_failed", detail={}, created_at=now))
        if not accepted:
            raise HTTPException(401, "Invalid credentials")
        return self.issue_access(username, current["role_id"])

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
            # A no-op write serializes rotation on SQLite, PostgreSQL and SQL Server.
            # SQL Server does not implement SQLAlchemy's SELECT FOR UPDATE clause.
            connection.execute(update(db.refresh_tokens).where(db.refresh_tokens.c.id == hashed)
                               .values(id=db.refresh_tokens.c.id))
            row = connection.execute(select(db.refresh_tokens).where(db.refresh_tokens.c.id == hashed)).mappings().first()
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
