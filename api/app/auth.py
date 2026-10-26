import hashlib
import secrets
import time
from dataclasses import dataclass

import jwt
from fastapi import HTTPException


@dataclass(frozen=True)
class Principal:
    username: str
    role: str


class Auth:
    def __init__(self, settings):
        self.settings = settings
        self.salt = secrets.token_bytes(16)
        self.accounts = {
            settings.demo_username: ("demo", self.digest(settings.demo_password)),
            settings.admin_username: ("admin", self.digest(settings.admin_password)),
        }
        self.dummy = self.digest(secrets.token_urlsafe(24))

    def digest(self, password):
        return hashlib.scrypt(password.encode(), salt=self.salt, n=16384, r=8, p=1)

    def login(self, username, password):
        account = self.accounts.get(username)
        expected = account[1] if account else self.dummy
        valid = secrets.compare_digest(expected, self.digest(password))
        if not account or not valid:
            raise HTTPException(401, "Invalid credentials")
        now = int(time.time())
        payload = {"sub": username, "role": account[0], "iat": now, "nbf": now,
                   "exp": now + self.settings.token_minutes * 60,
                   "iss": "servicestock", "aud": "servicestock-api"}
        return jwt.encode(payload, self.settings.jwt_secret, algorithm="HS256")

    def authenticate(self, token):
        try:
            payload = jwt.decode(token, self.settings.jwt_secret, algorithms=["HS256"],
                                 issuer="servicestock", audience="servicestock-api",
                                 options={"require": ["sub", "role", "iat", "nbf", "exp", "iss", "aud"]})
            account = self.accounts.get(payload["sub"])
            if not account or payload["role"] != account[0]:
                raise ValueError("Unknown account or role")
            return Principal(payload["sub"], payload["role"])
        except (jwt.InvalidTokenError, ValueError, TypeError):
            raise HTTPException(401, "Authentication required", headers={"WWW-Authenticate": "Bearer"}) from None
