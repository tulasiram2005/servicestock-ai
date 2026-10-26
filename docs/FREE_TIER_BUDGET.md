# Free-tier budget

Documentation checked 2026-10-26. Re-check before deploying; account eligibility is not verified.

| Service | Assumption / limit | Verified on | Control | Measured usage / exhaustion |
|---|---|---|---|---|
| Render Free | 750 instance-hours/workspace/month; sleeps after 15 idle minutes; ephemeral disk | 2026-10-26 https://render.com/docs/free | one API, no pingers, no disk state | Not deployed; account hours/bandwidth not measured. Without payment method, excess usage can suspend services/builds. |
| Neon Free | Official page currently lists 1 GB storage and 100 CU-hours/project/month; project retains stricter requested 0.5 GB cap and 350 MB target | 2026-10-26 https://neon.com/pricing | DB_TARGET_BYTES, DB_LIMIT_BYTES, retention, compact artifacts | See results/local_integration.json for local DB bytes; cloud CU-hours not measured |
| Vercel Hobby | Personal non-commercial use; page lists 100 GB fast transfer and 1M function invocations | 2026-10-26 https://vercel.com/docs/plans/hobby | light proxy only, no heavy compute | Not deployed; usage not measured; features may pause on exhaustion |
| GitHub Actions | Standard hosted runners free for public repositories; artifact/cache quotas still need account review | 2026-10-26 https://docs.github.com/en/billing/concepts/product-billing/github-actions | compute disabled until FREE_COMPUTE_ENABLED=true; 20-minute timeout, 3-day artifacts | Remote runs: none |
| Gemini / compatible endpoint | Model/account-specific quotas | Not verified | External calls disabled; LLM daily caps default zero | No calls; MockLLM works offline |
| Local Docker | No cloud service charges | 2026-10-26 local run | Local Postgres and bundled artifacts | Local CPU/disk use; no claimed cloud capacity |

Provider usage is not inferred from application request counts. DB size includes PostgreSQL
overhead. Retention does not immediately reclaim file bytes; VACUUM behavior must be measured.
DB_LIMIT_BYTES is a configured budget reference; enqueue currently stops at the lower target.
Default no-card/no-billing path is local Docker. Do not add a payment method to bypass free limits.
