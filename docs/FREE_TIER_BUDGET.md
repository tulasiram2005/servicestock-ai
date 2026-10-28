# Free-tier budget

Documentation checked 2026-10-28. Re-check before deploying; account eligibility is not verified.

| Service | Assumption / limit | Verified on | Control | Measured usage / exhaustion |
|---|---|---|---|---|
| Render Free | 750 instance-hours/workspace/month; sleeps after 15 idle minutes; ephemeral disk | 2026-10-28 https://render.com/docs/free | one API, no pingers, no disk state | Not deployed; account hours/bandwidth not measured. Without payment method, excess usage can suspend services/builds. |
| Neon Free | Official page currently lists 1 GB storage and 100 CU-hours/project/month; project retains stricter requested 0.5 GB cap and 350 MB target | 2026-10-28 https://neon.com/pricing | DB_TARGET_BYTES, DB_LIMIT_BYTES, retention, compact artifacts | See results/local_integration.json for local DB bytes; cloud CU-hours not measured |
| Vercel Hobby | Personal non-commercial use; page lists 100 GB fast transfer and 1M function invocations | 2026-10-28 https://vercel.com/docs/plans/hobby | light proxy only, no heavy compute | Not deployed; usage not measured; features may pause on exhaustion |
| GitHub Actions | Standard public-repository runners free; private repository uses included account allowance, verified before each manual run | 2026-10-28 https://docs.github.com/en/billing/concepts/product-billing/github-actions | compute disabled until FREE_COMPUTE_ENABLED=true; 20-minute timeout, 3-day artifacts | Expanded SQL Server run 40618520967 passed; pre-run UI showed 14/3,000 minutes used and $0 billable usage. Existing $0 budget unchanged |
| Gemini / compatible endpoint | Model/account-specific quotas | 2026-10-27 model documentation and user free-tier confirmation | Default calls disabled; LLM daily caps default zero | Live public Gemini routing and synthetic classification passed; normal app defaults remain Mock and zero caps |
| Local Docker | No cloud service charges | 2026-10-28 local run | Local Postgres and bundled artifacts | Local CPU/disk use; no claimed cloud capacity |

Provider usage is not inferred from application request counts. DB size includes PostgreSQL
overhead. Retention does not immediately reclaim file bytes; VACUUM behavior must be measured.
DB_LIMIT_BYTES is a configured budget reference; enqueue currently stops at the lower target.
Default no-card/no-billing path is local Docker. Do not add a payment method to bypass free limits.

Recheck sources on 2026-10-28: [Render](https://render.com/docs/free),
[Neon](https://neon.com/pricing), [Vercel Hobby](https://vercel.com/docs/plans/hobby).
Render explicitly describes Free as suitable for demos, not production, and may suspend
services for high outbound traffic (including external database traffic). Without a payment
method, bandwidth exhaustion suspends services and pipeline exhaustion disables builds.
Neon advertises no-card Free; this does not confirm this user's account/project state.
Vercel Hobby is personal/non-commercial only; usage exhaustion usually pauses features.
No account plan was upgraded, card entered, or hosting resource created during this check.
