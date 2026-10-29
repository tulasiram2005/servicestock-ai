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
quota concurrency passed in the targeted SQL Server workflow. No background quota polling occurs.

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

### Reproducible live-check preparation

`PYTHONPATH=api api/.venv/bin/python scripts/check_gemini.py --env-file .env`
performs configuration checks only. It never creates a network client. Add `--live`
only after the model's current free-tier availability and billing-disabled project are
verified. The live check permits one app-authored KPI prompt, reserves a single attempt,
prints only a sanitized outcome, and exits nonzero on fallback/unexpected routing. It
neither edits `.env` nor changes the running application's Mock default. Repeated manual
invocations each have a fresh one-attempt budget; this is a smoke tool, not a scheduler.

On 2026-10-27 the root environment file preflight reported missing key, model and local
confirmation flag. The user's verbal billing confirmation is recorded, but no key file
has been identified. Zero requests were attempted. Do not paste keys in chat; configure
them locally. The `.env.example` lists names only, with an empty key and confirmation false.

### Private terminal setup (2026-10-27)

Run `api/.venv/bin/python scripts/configure_gemini.py` from the repository in Terminal.
Enter a verified free-tier model ID, confirm billing is disabled, and paste the key at
its hidden prompt. The script makes no network calls and exclusively creates `.env.gemini`
with owner-only permissions (0600). It refuses existing files/symlinks and multiline input;
Git ignores this file. Do not paste the key in chat or supply it as a command argument.
Then run the check with `--env-file .env.gemini`. Application Mock defaults remain unchanged.

The user's screenshot shows the ServiceStock-AI project on Free tier; the user clarified
that the key was only copied, never saved locally. On 2026-10-27 the official
[pricing page](https://ai.google.dev/gemini-api/docs/pricing) lists standard text input/output
for `gemini-3.5-flash-lite` as free on Free tier. Project quota/access still needs a live
check. Use no grounding, caching, or paid upgrade. The smoke sends only app-authored public text.

### Live result — supersedes earlier missing-key status

On 2026-10-27 at 16:08 IST, one live `gemini-3.5-flash-lite` request passed in 1.603
seconds using the privately saved `.env.gemini`. The typed response selected `get_kpis`
for the public smoke prompt. See results/gemini_live_smoke.json. This is one routing
smoke, not a quality benchmark. No keys were logged or committed. Application defaults
remain Mock with zero quotas; the saved configuration is used only by the explicit checker.

### Ordered fallback and observed capabilities · 2026-10-27

`LLM_PROVIDER_ORDER=gemini,openai-local,ollama,mock` now tries each configured
adapter once in order. Any unique subset ending in `mock` is accepted, subject to the
existing provider prerequisites. Local providers remain development-only. No arbitrary
community URL is accepted, and defaults remain mock with zero caps.

All attempts share the same user/global budget; trying another provider cannot bypass
the cap. Each provider has its own 60-second failure cooldown and user-isolated route
cache. The Gemini public-prompt restriction is applied before every Gemini attempt, even
when it is in a chain. Private questions may reach a configured local model but never
Google. The response names the successful adapter using request-context-local provenance.

Admin usage includes per-provider observed JSON-plan capability: `unprobed`,
`validated_json_plan`, or `unavailable_or_invalid_output`. These states arise from real
responses, without extra probe requests, and describe this process's last observation.
They do not detect native tool support: native calling stays disabled. Unsupported JSON
or provider errors move to the next adapter, then deterministic summaries. Full native
tool negotiation, community endpoints, token accounting, and hard deadlines still remain.
Tests exercise 429 fallback, third-provider success, private-input isolation, shared caps,
cache/cooldown behavior and truthful response labels with simulated HTTP responses.
No live provider requests were needed for this change.

### Provider-reported token observations · 2026-10-28

Admin usage now includes current-process-lifetime token observations for Gemini, native
Ollama and local OpenAI-compatible responses. Input/output/total counts are retained when
reported; Gemini thinking counts are separate. No total is inferred by adding fields.
Each field records a sum and how many responses supplied a valid value. Missing or invalid
counts remain absent rather than zero. Cached routes do not add usage. Invalid tool plans
still contribute usage when the provider response contains valid metadata. Transport errors
and unparseable envelopes cannot provide token evidence. Counts reset with the process and
are not shared persistent daily quotas; the existing shared call-attempt limits remain.
`cost_usd` stays null: token counts cannot establish billing or free-tier eligibility.

Response field references checked 2026-10-28:
- https://ai.google.dev/api/generate-content
- https://docs.ollama.com/api/chat
- https://docs.ollama.com/api/openai-compatibility

Tests use synthetic HTTP responses; no extra live model request was sent. Persistent
token budgets, billing reconciliation, native-tool negotiation and hard deadlines remain
outside this implementation.

### Concurrent route admission · 2026-10-28

`LLM_MAX_CONCURRENT` defaults to 1 and accepts integers 1–4. One slot covers the whole
ordered provider chain and is released even on unexpected exceptions. When all slots
are occupied, routing immediately falls back to the offline assistant, before quota
reservation or a network request. There is no waiting queue. Cached routes also pass
through admission. This limit is per process, not distributed; use a single API process
for the free deployment. Admin metrics report the limit, scope and busy-fallback count.
Existing shared daily attempt limits still apply independently. This does not add native
tool negotiation or hard cancellation deadlines. No paid or live model calls were made.

### Tool execution deadlines · 2026-10-29

Tool execution now has a five-second per-tool and fifteen-second shared-chain
budget measured with a monotonic clock. An expired budget prevents dispatch;
a tool returning after its deadline is rejected with 504 and logged as timeout.
The remaining chain does not run. Tests inject a clock and slow dispatch functions.
These are cooperative boundaries, not thread cancellation: a running synchronous
operation must return (database statement timeouts remain the lower-level guard).
A report already enqueued is not rolled back. Native tool negotiation and durable
token budgets remain outstanding; this change does not claim those are complete.

### Durable output allowances · 2026-10-29

Optional LLM_OUTPUT_TOKEN_GLOBAL_CAP and LLM_OUTPUT_TOKEN_USER_CAP enforce
shared daily reservations in the existing quota table. Set both to positive
values to enable this extra guard; both zero preserves existing call-only limits.
Each uncached provider attempt reserves its maximum 1024 output tokens atomically
with global/user call counters. Denial rolls back every increment. Reservations
persist across restarts, reset by UTC day and are never refunded for failed or
short responses. If either allowance is enabled, a missing database fails closed.
Usage reports reserved_output_tokens separately from provider-reported consumption.
This conservative allowance excludes input/hidden reasoning tokens and is not a
billing ceiling. Existing free-tier confirmation and zero default call limits apply.
No schema migration is needed; hashed token-user subjects fit the existing 64-character
column. Native tool negotiation and additional adapters remain outstanding.
