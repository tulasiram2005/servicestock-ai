"""Run with PYTHONPATH=api; no downloads, keys or hosted model calls."""
import argparse
import json
import secrets
import time
from datetime import datetime, timezone
from app.assistant import REGISTRY
from app.config import Settings
from app.llm_router import LocalToolRouter

parser = argparse.ArgumentParser()
parser.add_argument('--model', required=True)
args = parser.parse_args()
settings = Settings(jwt_secret=secrets.token_urlsafe(48), demo_password=secrets.token_urlsafe(24),
    admin_password=secrets.token_urlsafe(24), llm_provider_order='ollama,mock', ollama_model=args.model,
    llm_global_daily_cap=1, llm_user_daily_cap=1)
started = time.monotonic()
calls, notice = LocalToolRouter(settings).route('local-verification','Show inventory KPIs',REGISTRY)
print(json.dumps({'measured_at':datetime.now(timezone.utc).isoformat(),'model':args.model,
    'provider':'ollama-local','elapsed_seconds':round(time.monotonic()-started,3),
    'validated_tools':[call[0] for call in calls] if calls else [],'fallback':calls is None,
    'notice':notice,'external_calls':0,'scope':'single routing prompt, not a quality benchmark'}))
