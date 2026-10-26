import hashlib
import json
import logging
import time

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, ConfigDict, Field

from .auth import Auth
from .config import Settings
from .runtime import MemoryRateLimiter, Metrics, TTLCache


class Prompt(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: str = Field(min_length=1, max_length=4000)


class Login(BaseModel):
    model_config = ConfigDict(extra="forbid")
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=256)


class MockLLM:
    def respond(self, prompt: str):
        return {"provider": "mock", "is_mock": True, "fallback": True,
                "notice": "Offline deterministic mode; no external model was called.",
                "answer": "No analytical results have been loaded yet.",
                "input_characters": len(prompt)}


def create_app(settings=None):
    settings = settings or Settings.from_env()
    app = FastAPI(title="ServiceStock AI", version="0.2.0", docs_url=None, redoc_url=None, openapi_url=None)
    app.add_middleware(CORSMiddleware, allow_origins=list(settings.allowed_origins),
                       allow_methods=["GET", "POST"], allow_headers=["Authorization", "Content-Type", "If-None-Match"],
                       expose_headers=["ETag", "Retry-After"])
    bearer = HTTPBearer(auto_error=False)
    auth = Auth(settings)
    limiter = MemoryRateLimiter(limit=settings.rate_limit)
    login_limiter = MemoryRateLimiter(limit=settings.login_rate_limit)
    cache = TTLCache(settings.cache_entries, settings.cache_seconds)
    metrics = Metrics()
    provider = MockLLM()
    logger = logging.getLogger("servicestock")

    def authorize(credentials: HTTPAuthorizationCredentials | None = Depends(bearer)):
        if credentials is None:
            raise HTTPException(401, "Authentication required", headers={"WWW-Authenticate": "Bearer"})
        principal = auth.authenticate(credentials.credentials)
        if not limiter.allow(principal.username):
            raise HTTPException(429, "Request limit reached", headers={"Retry-After": "60"})
        return principal

    def administrator(principal=Depends(authorize)):
        if principal.role != "admin":
            raise HTTPException(403, "Administrator access required")
        return principal

    @app.middleware("http")
    async def security_headers(request, call_next):
        started = time.monotonic()
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers.setdefault("Cache-Control", "no-store")
        response.headers["X-Frame-Options"] = "DENY"
        elapsed = time.monotonic() - started
        metrics.observe(response.status_code, elapsed)
        route = request.scope.get("route")
        logger.info(json.dumps({"event": "request", "route": getattr(route, "path", "unmatched"),
                               "status": response.status_code, "duration_ms": round(elapsed * 1000, 3)}))
        return response

    @app.get("/health")
    @app.get("/health/live")
    def live():
        return {"status": "ok"}

    @app.post("/api/auth/login")
    def login(body: Login):
        if not login_limiter.allow():
            raise HTTPException(429, "Please wait before signing in again", headers={"Retry-After": "60"})
        return {"access_token": auth.login(body.username, body.password), "token_type": "bearer",
                "expires_in": settings.token_minutes * 60}

    @app.get("/api/me")
    def me(principal=Depends(authorize)):
        return {"username": principal.username, "role": principal.role}

    @app.get("/api/status")
    def status(request: Request, principal=Depends(authorize)):
        data = {"stage": "foundation", "llm_provider": "mock", "database_connected": False,
                "specification_available": False, "metrics": None, "free_tier_demo": True,
                "synthetic_cost_assumptions": True, "uploads_enabled": False}
        payload = json.dumps(data, sort_keys=True).encode()
        etag = '"' + hashlib.sha256(payload).hexdigest() + '"'
        headers = {"ETag": etag, "Cache-Control": "private, no-cache"}
        if request.headers.get("if-none-match") == etag:
            return Response(status_code=304, headers=headers)
        return Response(payload, media_type="application/json", headers=headers)

    @app.get("/metrics", dependencies=[Depends(administrator)])
    def measured_metrics():
        return metrics.snapshot()

    @app.post("/api/assistant")
    def assistant(prompt: Prompt, principal=Depends(authorize)):
        key = hashlib.sha256((principal.username + "\0" + prompt.text).encode()).hexdigest()
        result = cache.get(key)
        if result is None:
            result = provider.respond(prompt.text)
            cache.put(key, result)
        return result

    app.state.authorize = authorize
    app.state.administrator = administrator
    return app
