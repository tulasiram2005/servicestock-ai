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

Attempts are reserved atomically before calls. Caps are per process per UTC day, reset on
restart, and are not distributed billing controls. Model routing caches are user-specific
and bounded. Failures/429s trigger a 60-second circuit cooldown rather than repeated calls.
HTTP phase timeouts are five seconds; response reads enforce a byte cap and check elapsed
time between chunks. These are not a hard process-cancellation deadline. Metrics are
available to administrators at `/api/admin/llm-usage`.

Offline tests use HTTP mock responses for valid/invalid tool plans, 429/500/redirect failures,
cache isolation, concurrent cap enforcement and day rollover. A live Ollama model has not
been run or quality-evaluated. Native tool capability negotiation, Gemini/OpenAI-compatible
adapters, persistent distributed budgets and per-tool cancellation remain pending.

Protocol reference checked 2026-10-27:
[Ollama official API](https://github.com/ollama/ollama/blob/main/docs/api.md).
The implementation uses `/api/chat`, non-streaming JSON mode and bounded generation.
