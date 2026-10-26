# ServiceStock AI

Initial implementation from the confirmed requirements in the current chat.
The original uploaded specification and detailed FREE-TIER ONLY overrides were
not returned by the referenced conversation. This is a foundation, not completed
P0 acceptance or a completed application.

## Available now

FastAPI with fail-closed token configuration, protected status and assistant
endpoints, bounded prompt validation, a bounded in-process rate limiter, and an
explicit offline MockLLM. No customer input is echoed by the mock. No model
quality or financial performance metrics are invented.

## Run locally

From `api`, create a virtual environment and install `requirements-dev.txt`.
Set `API_TOKEN` to a randomly generated secret of at least 32 characters, then:

```sh
uvicorn app.main:create_app --factory --host 127.0.0.1 --port 8000
python -m pytest -q
```

Pass the token as an Authorization Bearer header for `/api/status` and
`/api/assistant`. This is foundation service authentication; user accounts,
roles, tenant isolation, and production authentication remain pending the spec.
Never place this service token in browser code or a public environment variable.

See `docs/STATUS.md` for constraints and remaining work.
