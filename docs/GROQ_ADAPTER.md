# Optional Groq free-plan adapter

Implemented 2026-10-29; disabled by default. This is an additional remote
OpenAI-compatible adapter, not an OpenAI paid API connection.

Before enabling, verify the account is on the Free plan with no billing upgrade
and that the explicitly selected model has free quota. Current reference checked
2026-10-29: https://console.groq.com/docs/rate-limits and
https://console.groq.com/docs/api-reference . Account eligibility has not been
verified and no live Groq request was made.

Configure privately: GROQ_API_KEY, GROQ_MODEL, GROQ_FREE_TIER_CONFIRMED=true,
LLM_PROVIDER_ORDER=groq,mock and small positive LLM_GLOBAL_DAILY_CAP and
LLM_USER_DAILY_CAP. Default caps remain zero. Never commit the key.
The confirmation flag is an operator assertion, not automatic billing detection.

Only app-authored inventory KPI and data-quality prompts leave the process.
Arbitrary user prompts are rejected before reserving quota. Uploads must remain
disabled. HTTPS destination is fixed; redirects and environment proxies are off.
Existing response limits, concurrency, durable budget reservations, cooldown,
allowlisted tool validation and deterministic fallback apply. LLM_NATIVE_TOOLS
opts into native function calls; capability is reported only after valid output.
No model is automatically selected, downloaded, subscribed to or upgraded.

Mock-transport tests cover native and JSON responses, credential redaction,
private prompt refusal, and redirect/rate-limit/server-error fallback. These
prove adapter behavior, not live model availability or quality.
