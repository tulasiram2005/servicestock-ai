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
cache isolation, concurrent cap enforcement and day rollover. A live Ollama model has not
been run or quality-evaluated. Native tool capability negotiation, external Gemini/community adapters, provider token/cost
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
