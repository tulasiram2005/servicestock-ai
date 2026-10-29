import os
import re
from dataclasses import dataclass, field
from urllib.parse import urlsplit, parse_qs


@dataclass(frozen=True)
class Settings:
    jwt_secret: str = field(repr=False)
    demo_password: str = field(repr=False)
    admin_password: str = field(repr=False)
    database_url: str = field(default="", repr=False)
    environment: str = "local"
    demo_username: str = "demo"
    admin_username: str = "admin"
    token_minutes: int = 15
    rate_limit: int = 60
    login_rate_limit: int = 10
    cache_seconds: int = 30
    cache_entries: int = 256
    retention_days: int = 30
    db_target_bytes: int = 350_000_000
    db_limit_bytes: int = 500_000_000
    statement_timeout_ms: int = 5000
    worker_mode: str = "embedded"
    job_lease_seconds: int = 60
    job_max_attempts: int = 3
    job_retry_seconds: int = 2
    jobs_max_pending: int = 100
    uploads_enabled: bool = False
    allowed_origins: tuple[str, ...] = ("http://localhost:3000",)
    llm_global_daily_cap: int = 0
    llm_user_daily_cap: int = 0
    llm_max_concurrent: int = 1
    llm_output_token_global_cap: int = 0
    llm_output_token_user_cap: int = 0
    llm_provider_order: str = 'mock'
    llm_native_tools: bool = False
    ollama_model: str = ''
    gemini_api_key: str = field(default='', repr=False)
    gemini_model: str = ''
    gemini_free_tier_confirmed: bool = False
    groq_api_key: str = field(default='', repr=False)
    groq_model: str = ''
    groq_free_tier_confirmed: bool = False

    def __post_init__(self):
        if type(self.llm_max_concurrent) is not int or not 1 <= self.llm_max_concurrent <= 4:
            raise ValueError("LLM_MAX_CONCURRENT must be an integer from 1 to 4")
        providers = self.llm_provider_order.split(',')
        if (providers[-1] != 'mock' or len(set(providers)) != len(providers)
                or any(name not in {'mock', 'ollama', 'openai-local', 'gemini', 'groq'} for name in providers)):
            raise ValueError('Provider order must contain unique supported providers and end with mock')
        local = bool({'ollama', 'openai-local'} & set(providers))
        if local and (not self.ollama_model or 'cloud' in self.ollama_model.lower() or len(self.ollama_model) > 120):
            raise ValueError('Ollama requires an explicitly configured local model')
        if 'groq' in providers:
            if not self.groq_api_key or not self.groq_free_tier_confirmed or self.uploads_enabled:
                raise ValueError('Groq requires a key, verified free-tier configuration and disabled uploads')
            if not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9/_.-]{0,119}', self.groq_model):
                raise ValueError('Configure an explicit Groq model ID')
        if 'gemini' in providers:
            if not self.gemini_api_key or not self.gemini_free_tier_confirmed or self.uploads_enabled:
                raise ValueError('Gemini requires a key, verified free-tier configuration and disabled uploads')
            if not re.fullmatch(r'gemini-[a-z0-9.-]*flash[a-z0-9.-]*', self.gemini_model):
                raise ValueError('Configure an explicit Gemini Flash model ID')
        if self.environment == 'production' and local:
            raise ValueError('Local model routing is development-only')
        if len(self.jwt_secret) < 32:
            raise ValueError("JWT_SECRET must contain at least 32 characters")
        if min(len(self.demo_password), len(self.admin_password)) < 12:
            raise ValueError("DEMO_PASSWORD and ADMIN_PASSWORD must contain at least 12 characters")
        if self.demo_password == self.admin_password or self.demo_username == self.admin_username:
            raise ValueError("Demo and administrator credentials must be distinct")
        if self.environment not in {"local", "test", "production"}:
            raise ValueError("APP_ENV must be local, test, or production")
        if self.worker_mode not in {"embedded", "standalone", "disabled"}:
            raise ValueError("Invalid WORKER_MODE")
        for name in ("token_minutes", "rate_limit", "login_rate_limit", "cache_seconds",
                     "cache_entries", "retention_days", "db_target_bytes", "db_limit_bytes",
                     "statement_timeout_ms", "job_lease_seconds", "job_max_attempts",
                     "job_retry_seconds", "jobs_max_pending"):
            if getattr(self, name) <= 0:
                raise ValueError(f"{name} must be positive")
        if self.db_target_bytes >= self.db_limit_bytes:
            raise ValueError("DB target must be smaller than the configured limit")
        if min(self.llm_global_daily_cap, self.llm_user_daily_cap, self.llm_output_token_global_cap, self.llm_output_token_user_cap) < 0:
            raise ValueError("LLM caps cannot be negative")
        if self.environment == "production":
            if self.uploads_enabled:
                raise ValueError("Public deployment must disable uploads")
            if not self.database_url.startswith("postgresql+psycopg://"):
                raise ValueError("Production requires pooled PostgreSQL")
            parsed = urlsplit(self.database_url)
            if not parsed.hostname or "-pooler." not in parsed.hostname:
                raise ValueError("Production requires a Neon pooled hostname")
            query = parse_qs(parsed.query, keep_blank_values=True)
            if query.get("sslmode") not in (["require"], ["verify-full"]):
                raise ValueError("Production database requires TLS")
            if not self.allowed_origins or any(
                urlsplit(origin).scheme != "https" or not urlsplit(origin).hostname
                or urlsplit(origin).username is not None or urlsplit(origin).password is not None
                or urlsplit(origin).path not in {"", "/"} or urlsplit(origin).query or urlsplit(origin).fragment
                for origin in self.allowed_origins):
                raise ValueError("Production origins must use HTTPS")

    @classmethod
    def from_env(cls):
        values = {
            "jwt_secret": os.getenv("JWT_SECRET", ""),
            "demo_password": os.getenv("DEMO_PASSWORD", ""),
            "admin_password": os.getenv("ADMIN_PASSWORD", ""),
            "database_url": os.getenv("DATABASE_URL", ""),
            "environment": os.getenv("APP_ENV", "local"),
            "demo_username": os.getenv("DEMO_USERNAME", "demo"),
            "admin_username": os.getenv("ADMIN_USERNAME", "admin"),
            "worker_mode": os.getenv("WORKER_MODE", "embedded"),
            "llm_native_tools": os.getenv("LLM_NATIVE_TOOLS", "false").lower() == "true",
            "llm_provider_order": os.getenv("LLM_PROVIDER_ORDER", "mock"),
            "ollama_model": os.getenv("OLLAMA_MODEL", ""),
            "gemini_api_key": os.getenv("GEMINI_API_KEY", ""),
            "gemini_model": os.getenv("GEMINI_MODEL", ""),
            "gemini_free_tier_confirmed": os.getenv("GEMINI_FREE_TIER_CONFIRMED", "false").lower() == "true",
            "groq_api_key": os.getenv("GROQ_API_KEY", ""),
            "groq_model": os.getenv("GROQ_MODEL", ""),
            "groq_free_tier_confirmed": os.getenv("GROQ_FREE_TIER_CONFIRMED", "false").lower() == "true",
            "uploads_enabled": os.getenv("UPLOADS_ENABLED", "false").lower() == "true",
            "allowed_origins": tuple(filter(None, (value.strip() for value in os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")))),
        }
        for name in ("token_minutes", "rate_limit", "login_rate_limit", "cache_seconds",
                     "cache_entries", "retention_days", "db_target_bytes", "db_limit_bytes",
                     "statement_timeout_ms", "job_lease_seconds", "job_max_attempts",
                     "job_retry_seconds", "jobs_max_pending", "llm_global_daily_cap", "llm_user_daily_cap", "llm_max_concurrent", "llm_output_token_global_cap", "llm_output_token_user_cap"):
            if name.upper() in os.environ:
                values[name] = int(os.environ[name.upper()])
        return cls(**values)
