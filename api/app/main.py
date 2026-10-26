import os
import secrets
import time
from collections import deque
from dataclasses import dataclass, field
from threading import Lock

from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field


@dataclass(frozen=True)
class Settings:
    api_token: str = field(repr=False)
    environment: str = "local"

    @classmethod
    def from_env(cls):
        token = os.getenv("API_TOKEN", "")
        if len(token) < 32:
            raise ValueError("API_TOKEN must contain at least 32 characters")
        return cls(api_token=token, environment=os.getenv("APP_ENV", "local"))


class Prompt(BaseModel):
    text: str = Field(min_length=1, max_length=4000)


class MockLLM:
    def respond(self, prompt: str):
        return {
            "provider": "mock",
            "is_mock": True,
            "answer": "Offline assistant is available. No model inference was performed.",
            "input_characters": len(prompt),
        }


class RateLimiter:
    def __init__(self, limit=30, window=60, clock=time.monotonic):
        self.limit = limit
        self.window = window
        self.clock = clock
        self.events = deque()
        self.lock = Lock()

    def allow(self):
        with self.lock:
            now = self.clock()
            while self.events and self.events[0] <= now - self.window:
                self.events.popleft()
            if len(self.events) >= self.limit:
                return False
            self.events.append(now)
            return True


def create_app(settings=None):
    settings = settings or Settings.from_env()
    app = FastAPI(title="ServiceStock AI", version="0.1.0", docs_url=None, redoc_url=None, openapi_url=None)
    bearer = HTTPBearer(auto_error=False)
    limiter = RateLimiter()
    provider = MockLLM()

    def authorize(credentials: HTTPAuthorizationCredentials | None = Depends(bearer)):
        if credentials is None or not secrets.compare_digest(credentials.credentials, settings.api_token):
            raise HTTPException(401, "Authentication required", headers={"WWW-Authenticate": "Bearer"})
        if not limiter.allow():
            raise HTTPException(429, "Request limit reached", headers={"Retry-After": "60"})

    @app.middleware("http")
    async def security_headers(request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Frame-Options"] = "DENY"
        return response

    @app.get("/health/live")
    def live():
        return {"status": "ok"}

    @app.get("/api/status", dependencies=[Depends(authorize)])
    def status():
        return {
            "stage": "foundation",
            "llm_provider": "mock",
            "database_connected": False,
            "specification_available": False,
            "metrics": None,
        }

    @app.post("/api/assistant", dependencies=[Depends(authorize)])
    def assistant(prompt: Prompt):
        return provider.respond(prompt.text)

    return app
