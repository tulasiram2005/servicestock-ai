"""Explicit hosted smoke check; never prints credentials, cookies or response bodies."""
import argparse
import json
from pathlib import Path

import httpx

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--approved-demo-login', action='store_true', required=True,
                    help='Confirm authorization to send the demo password through the hosted frontend')
args = parser.parse_args()
root = Path(__file__).resolve().parents[1]
values = dict(line.split('=', 1) for line in (root / '.env.hosted').read_text().splitlines()
              if '=' in line and not line.startswith('#'))
frontend = 'https://servicestock-ai.vercel.app'
backend = 'https://servicestock-ai-api.onrender.com'
checks = {}
expected = {'backend_ready': 200, 'frontend': 200, 'login': 200, 'me': 200,
            'status': 200, 'parts': 200, 'kpis': 200, 'dq': 200, 'results': 200,
            'admin/users': 403, 'refresh': 200, 'logout': 200}
try:
    with httpx.Client(timeout=45) as client:
        checks['backend_ready'] = client.get(backend + '/ready').status_code
        checks['frontend'] = client.get(frontend).status_code
        response = client.post(frontend + '/api/auth/login', json={
            'username': values.get('DEMO_USERNAME', 'demo'), 'password': values['DEMO_PASSWORD']})
        checks['login'] = response.status_code
        if response.status_code == 200:
            headers = {'Authorization': 'Bearer ' + response.json()['access_token']}
            for route in ('me', 'status', 'parts', 'kpis', 'dq', 'results', 'admin/users'):
                checks[route] = client.get(frontend + '/api/' + route, headers=headers).status_code
            for action in ('refresh', 'logout'):
                checks[action] = client.post(frontend + '/api/auth/' + action, headers={
                    'Origin': frontend, 'x-csrf-token': client.cookies.get('csrf', '')}).status_code
except Exception as error:
    checks['error_type'] = type(error).__name__
passed = checks == expected
from datetime import datetime, timezone
report = {'checked_at': datetime.now(timezone.utc).isoformat(), 'frontend': frontend,
          'backend': backend, 'checks': checks, 'passed': passed,
          'scope': 'HTTP smoke only; not human browser accessibility or load certification'}
(root / 'results/hosted_smoke.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report))
raise SystemExit(0 if passed else 1)
