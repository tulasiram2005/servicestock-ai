import hashlib
import json
import logging
import time
import secrets
import sys
import uuid
import asyncio
import contextlib

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, ConfigDict, Field

from .auth import Auth
from .config import Settings
from .runtime import MemoryRateLimiter, Metrics, TTLCache
from .db.store import Store
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text
from .jobs import JobQueue, Worker
from .services import handle_job
from .api import router
from .assistant import Assistant
from fastapi.responses import StreamingResponse


class Prompt(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: str = Field(min_length=1, max_length=4000)
    session_id: str | None = Field(default=None, pattern=r"^[a-f0-9]{32}$")


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


def create_app(settings=None, store_override=None):
    settings = settings or Settings.from_env()
    app = FastAPI(title="ServiceStock AI", version="0.2.0", docs_url=None, redoc_url=None, openapi_url=None)
    app.add_middleware(CORSMiddleware, allow_origins=list(settings.allowed_origins),
                       allow_methods=["GET", "POST"], allow_headers=["Authorization", "Content-Type", "If-None-Match", "X-CSRF-Token"],
                       expose_headers=["ETag", "Retry-After"])
    bearer = HTTPBearer(auto_error=False)
    store = store_override or (Store(settings.database_url, settings.statement_timeout_ms) if settings.database_url else None)
    auth = Auth(settings, store)
    limiter = MemoryRateLimiter(limit=settings.rate_limit)
    login_limiter = MemoryRateLimiter(limit=settings.login_rate_limit)
    ip_limiter = MemoryRateLimiter(limit=settings.rate_limit * 3)
    cache = TTLCache(settings.cache_entries, settings.cache_seconds)
    metrics = Metrics()
    provider = MockLLM()
    queue = JobQueue(store, settings) if store else None
    worker = Worker(queue, lambda kind, payload: handle_job(store, settings, kind, payload)) if queue else None

    @contextlib.asynccontextmanager
    async def lifespan(application):
        loop = asyncio.get_running_loop()
        application.state.wake = lambda: loop.call_soon_threadsafe(worker.wake) if worker else None
        task = asyncio.create_task(worker.run()) if worker and settings.worker_mode == "embedded" else None
        yield
        if task:
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task
        if store:
            store.engine.dispose()

    app.router.lifespan_context = lifespan
    logger = logging.getLogger("servicestock")
    if not logger.handlers:
        logger.addHandler(logging.StreamHandler(sys.stdout))
    logger.setLevel(logging.INFO)
    logger.propagate = False

    @app.exception_handler(SQLAlchemyError)
    async def database_unavailable(request, error):
        return Response(json.dumps({"detail": "Database is waking up; please retry shortly"}), status_code=503,
                        media_type="application/json", headers={"Retry-After": "5"})

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
        if request.url.path.startswith("/api/") and not ip_limiter.allow(request.client.host if request.client else "unknown"):
            return Response(status_code=429, headers={"Retry-After": "60"})
        liveness_probe = request.method == "GET" and request.url.path in {"/health", "/health/live"}
        if settings.environment == "production" and request.url.scheme != "https" and not liveness_probe:
            return Response(status_code=400)
        if request.method in {"POST", "PUT", "PATCH"}:
            body = bytearray()
            async for chunk in request.stream():
                body.extend(chunk)
                if len(body) > 16384:
                    return Response(status_code=413)
            request._body = bytes(body)
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers.setdefault("Cache-Control", "no-store")
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["X-Request-ID"] = uuid.uuid4().hex
        if settings.environment == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
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

    @app.get("/ready")
    def ready():
        if store is None:
            raise HTTPException(503, "Database is not configured")
        with store.transaction() as connection:
            connection.execute(text("SELECT 1"))
        return {"status": "ready"}

    @app.post("/api/auth/login")
    def login(body: Login, response: Response):
        if not login_limiter.allow():
            raise HTTPException(429, "Please wait before signing in again", headers={"Retry-After": "60"})
        token = auth.login(body.username, body.password)
        set_cookies(response, auth.create_refresh(body.username))
        return {"access_token": token, "token_type": "bearer",
                "expires_in": settings.token_minutes * 60}

    def set_cookies(response, refresh):
        response.set_cookie("refresh", refresh, httponly=True, secure=settings.environment == "production",
                            samesite="strict", path="/api/auth", max_age=604800)
        response.set_cookie("csrf", secrets.token_urlsafe(24), httponly=False, secure=settings.environment == "production",
                            samesite="strict", path="/", max_age=604800)

    def csrf(request):
        cookie, header = request.cookies.get("csrf", ""), request.headers.get("x-csrf-token", "")
        if not cookie or not secrets.compare_digest(cookie, header) or request.headers.get("origin") not in settings.allowed_origins:
            raise HTTPException(403, "CSRF validation failed")

    @app.post("/api/auth/refresh")
    def refresh(request: Request, response: Response):
        csrf(request)
        token, replacement = auth.rotate(request.cookies.get("refresh", ""))
        set_cookies(response, replacement)
        return {"access_token": token, "token_type": "bearer", "expires_in": settings.token_minutes * 60}

    @app.post("/api/auth/logout")
    def logout(request: Request, response: Response):
        csrf(request)
        auth.logout(request.cookies.get("refresh", ""))
        response.delete_cookie("refresh", path="/api/auth")
        response.delete_cookie("csrf", path="/")
        return {"status": "signed_out"}

    @app.get("/api/me")
    def me(principal=Depends(authorize)):
        return {"username": principal.username, "role": principal.role}

    @app.get("/api/status")
    def status(request: Request, principal=Depends(authorize)):
        data = {"stage": "implementation", "llm_provider": "mock", "database_connected": bool(store),
                "specification_available": True, "metrics": None, "free_tier_demo": True,
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
        if store:
            return Assistant(store, queue, lambda: app.state.wake()).conversation(principal, prompt.text, prompt.session_id)
        key = hashlib.sha256((principal.username + "\0" + prompt.text).encode()).hexdigest()
        result = cache.get(key)
        if result is None:
            result = provider.respond(prompt.text)
            cache.put(key, result)
        return result

    @app.post("/api/assistant/stream")
    def assistant_stream(prompt: Prompt, principal=Depends(authorize)):
        result = assistant(prompt, principal)
        def events():
            for item in result.get("trace", []):
                yield "event: tool\ndata: " + json.dumps(item, default=str) + "\n\n"
            yield "event: answer\ndata: " + json.dumps(result, default=str) + "\n\n"
            yield "event: done\ndata: {}\n\n"
        return StreamingResponse(events(), media_type="text/event-stream", headers={"X-Accel-Buffering": "no", "Cache-Control": "no-store"})

    app.state.authorize = authorize
    app.state.administrator = administrator
    app.state.store = store
    app.state.auth = auth
    app.state.queue = queue
    app.include_router(router(store, settings, authorize, administrator, queue,
                              lambda: app.state.wake(), cache))
    return app
