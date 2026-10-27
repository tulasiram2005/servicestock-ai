"""Preflight by default; --live sends at most one app-authored public prompt.

Run: PYTHONPATH=api api/.venv/bin/python scripts/check_gemini.py --env-file .env
The environment file is parsed as data and is never executed as shell code.
"""
import argparse
import json
import secrets
import time
from datetime import datetime, timezone
from pathlib import Path

from app.config import Settings
from app.llm_router import LocalToolRouter
from app.assistant import REGISTRY


def read_config(path):
    allowed = {'GEMINI_API_KEY', 'GEMINI_MODEL', 'GEMINI_FREE_TIER_CONFIRMED'}
    values = {}
    for line in Path(path).read_text().splitlines():
        line = line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        key, value = line.split('=', 1)
        key, value = key.strip(), value.strip()
        if key not in allowed:
            continue
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        values[key] = value
    return values


def check(values, live=False, router_factory=LocalToolRouter):
    missing = [name for name in ('GEMINI_API_KEY', 'GEMINI_MODEL') if not values.get(name)]
    if values.get('GEMINI_FREE_TIER_CONFIRMED', '').lower() != 'true':
        missing.append('GEMINI_FREE_TIER_CONFIRMED=true')
    if missing:
        return {'status': 'configuration_required', 'missing': missing, 'requests_attempted': 0}, 2
    try:
        settings = Settings(jwt_secret=secrets.token_urlsafe(48),
            demo_password=secrets.token_urlsafe(24), admin_password=secrets.token_urlsafe(24),
            llm_provider_order='gemini,mock', gemini_api_key=values['GEMINI_API_KEY'],
            gemini_model=values['GEMINI_MODEL'], gemini_free_tier_confirmed=True,
            llm_global_daily_cap=1, llm_user_daily_cap=1, uploads_enabled=False)
    except ValueError:
        return {'status': 'invalid_configuration', 'requests_attempted': 0}, 2
    if not live:
        return {'status': 'ready_for_explicit_live_check', 'requests_attempted': 0,
                'billing_verification': 'operator assertion; not remotely checked'}, 0
    started = time.monotonic()
    router = router_factory(settings)
    try:
        calls, _ = router.route('public-smoke', 'Show inventory KPIs', REGISTRY)
        passed = bool(calls and all(name == 'get_kpis' for name, _ in calls))
        return {'status': 'passed' if passed else 'fallback_or_unexpected_route',
                'measured_at': datetime.now(timezone.utc).isoformat(),
                'elapsed_seconds': round(time.monotonic()-started, 3),
                'requests_attempted': router.usage()['external_calls'],
                'scope': 'single public routing prompt; not a model quality benchmark'}, 0 if passed else 1
    except Exception:
        # Never emit exception text: HTTP or provider errors may contain credentials.
        return {'status': 'validation_error', 'requests_attempted': 'unknown'}, 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--env-file', default='.env')
    parser.add_argument('--live', action='store_true')
    args = parser.parse_args()
    try:
        values = read_config(args.env_file)
    except (OSError, UnicodeError):
        print(json.dumps({'status': 'configuration_file_unreadable', 'requests_attempted': 0}))
        return 2
    result, code = check(values, args.live)
    print(json.dumps(result))
    return code


if __name__ == '__main__':
    raise SystemExit(main())
