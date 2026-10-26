# Assistant provider status

Default: `LLM_PROVIDER_ORDER=mock`, both daily caps zero. This makes no model requests.

Optional native local development: set `LLM_PROVIDER_ORDER=ollama,mock`, `OLLAMA_MODEL` to
an already installed local model, and positive `LLM_GLOBAL_DAILY_CAP` / `LLM_USER_DAILY_CAP`.
Run Ollama on 127.0.0.1:11434 with `OLLAMA_NO_CLOUD=1`; run the API on the same machine.
No model download or server is provisioned automatically. Docker-to-host model networking
is not implemented. This provider is rejected in production configuration.

Ollama proposes typed read-only tool calls; it cannot request report jobs. The existing
executor revalidates arguments, enforces roles/session ownership and logs tool execution.
Only deterministic, cited summaries of tool results reach the UI. Model-authored prose is
never rendered. Model routing is optional and failures return to deterministic routing.

Attempts are reserved atomically before calls. When a database is configured, global and
hashed-user UTC-day counters share one transaction and survive API restarts. A rejected user
reservation rolls back the global increment. Database errors fail closed to deterministic
routing. Retention removes old daily rows. Standalone use without a database retains a
per-process counter that resets on restart; its metrics explicitly identify that scope.
These count attempts, not token charges or provider billing. Model routing caches are user-specific
and bounded. Failures/429s trigger a 60-second circuit cooldown rather than repeated calls.
HTTP phase timeouts are five seconds; response reads enforce a byte cap and check elapsed
time between chunks. These are not a hard process-cancellation deadline. Metrics are
available to administrators at `/api/admin/llm-usage`.

Offline tests use HTTP mock responses for valid/invalid tool plans, 429/500/redirect failures,
cache isolation, concurrent cap enforcement and day rollover. A live Mistral local routing smoke was attempted on 2026-10-27; both cold and warm
attempts hit the five-second timeout and fell back. Model quality is not established. Native tool capability negotiation, external community adapters, provider token/cost
accounting and per-tool cancellation remain pending.
Local PostgreSQL concurrency verification is in results/llm_budget_postgres.json; SQL Server
quota concurrency remains unverified. No background quota polling occurs.

Protocol reference checked 2026-10-27:
[Ollama official API](https://github.com/ollama/ollama/blob/main/docs/api.md).
The implementation uses `/api/chat`, non-streaming JSON mode and bounded generation.


OpenAI-compatible local mode (2026-10-27): `LLM_PROVIDER_ORDER=openai-local,mock`
uses the same explicitly installed `OLLAMA_MODEL` at the fixed loopback endpoint
`http://127.0.0.1:11434/v1/chat/completions`. The request uses JSON object response mode,
non-streaming output, and a 1,024-token output cap. No API key is sent. This mode inherits
shared daily attempt budgets, strict tool validation, bounded response reads, cooldown,
and deterministic fallback. It is rejected in production, like the native Ollama mode.
Empty choices, missing/invalid content and disallowed tool plans fall back safely.
Usage reports explicitly identify `openai-local` and do not claim native tool calling.
Protocol checked against [Ollama's official compatibility documentation](https://github.com/ollama/ollama/blob/main/docs/api/openai-compatibility.mdx).
Tests use simulated HTTP responses; no actual model was downloaded or invoked. This is
not certification of arbitrary hosted endpoints, free-tier billing, or live model quality.


Gemini adapter (disabled by default; protocol tested 2026-10-27): select
`LLM_PROVIDER_ORDER=gemini,mock`, set `GEMINI_MODEL` to an explicitly verified free-tier
Flash model, provide `GEMINI_API_KEY` privately, and set `GEMINI_FREE_TIER_CONFIRMED=true`
only after checking that model/account is free and billing is disabled. Uploads must be
false. The confirmation is an operator assertion, not automated billing verification.
Zero call caps still prevent all calls. No key was discovered or used during implementation.
The API key is hidden from settings representations and sent only in the request header
at the fixed Google HTTPS endpoint. Redirects and proxy environment variables are disabled.

To enforce the public/synthetic-only requirement, only exact case-insensitive prompts
`show kpis`, `show inventory kpis`, and `show data quality` map to app-authored public text.
All other questions fall back before reservation or network activity. No usernames, uploaded
rows, tool results or arbitrary question text are sent. Returned plans still pass typed tool
validation and the role/ownership executor; model prose is never rendered. Empty, safety-
blocked, incomplete, malformed or error responses fall back. External attempt metrics are
explicitly process-local; daily total reservations remain shared when a database is used.

The [official Gemini generateContent API](https://ai.google.dev/api/generate-content)
was checked on 2026-10-27. Mock HTTP tests cover the request, secret isolation, input gate,
configuration safeguards and blocked/incomplete responses. Live Gemini requests were not
made; no free-tier account/model verification or paid billing activation occurred. General
free-text cloud routing, multi-provider cascades and native tool negotiation remain pending.

Live local evidence: `results/live_model_smoke.json`. Reproduce a single attempt with
`PYTHONPATH=api api/.venv/bin/python scripts/check_local_model.py --model mistral:latest`.
An already installed local model server is required; the script does not download models.
