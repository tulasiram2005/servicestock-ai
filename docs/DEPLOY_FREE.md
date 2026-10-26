# Free deployment guide (not deployed or verified end-to-end)

Local Docker is the verified default: make up. Read generated .env locally for credentials.
Do not paste secrets into chat or GitHub. Production deployment remains gated on security
review and account-specific no-card eligibility; this document is setup guidance, not evidence
of deployment.

1. Create a public GitHub repository after reviewing the files and dataset redistribution terms.
   Push the local commits. Use standard Linux Actions runners only; leave
   FREE_COMPUTE_ENABLED unset until storage and Actions quotas are checked.
2. Create a Neon Free project without a card. Copy the pooled hostname, enable TLS, and use
   DATABASE_URL with postgresql+psycopg:// and sslmode=require. Do not use a direct connection
   for the API. Run migrations and seed from a trusted local environment; do not expose DB URLs.
3. Create a Render Web Service, Docker, repository-root context, api/Dockerfile, Free instance.
   Do not enable a paid disk, worker, or plan. Set APP_ENV=production, DATABASE_URL,
   JWT_SECRET, DEMO_USERNAME/DEMO_PASSWORD, ADMIN_USERNAME/ADMIN_PASSWORD,
   ALLOWED_ORIGINS=https://your-project.vercel.app, WORKER_MODE=embedded,
   UPLOADS_ENABLED=false. Health check /health, not /ready; no external uptime pingers.
4. Create a Vercel Hobby personal/non-commercial project with root web. Set API_INTERNAL_URL
   to the Render HTTPS origin before building. Keep default vercel.app domain. Same-origin
   proxy supports Strict refresh cookies; verify forwarded scheme handling before release.
5. Optional Google AI Studio key: do not enable billing. External provider adapters are not
   yet implemented in this build; leave all provider keys absent and daily caps at zero.
6. Configure optional GitHub DATABASE_URL secret for compact result publishing only after
   migrations/seed. Set FREE_COMPUTE_ENABLED=true only for a reviewed public repository.
7. Verify login/refresh/logout, read-only demo, job ownership, report roles, synthetic badges,
   backend wake-up UI, DB wake-up latency and quota behavior with a few requests only.
   Record actual results. Do not mark deployment done until these checks pass.

## Configuration

See .env.example and api/app/config.py for the authoritative accepted variables.
Secrets: JWT_SECRET (>=32 characters), DEMO_PASSWORD/ADMIN_PASSWORD (>=12, distinct),
DATABASE_URL, POSTGRES_PASSWORD (Compose only). Generated demo/admin names default to demo/admin.
Operational: TOKEN_MINUTES, RATE_LIMIT, LOGIN_RATE_LIMIT, CACHE_SECONDS, CACHE_ENTRIES,
RETENTION_DAYS, DB_TARGET_BYTES, DB_LIMIT_BYTES, STATEMENT_TIMEOUT_MS, WORKER_MODE,
JOB_LEASE_SECONDS, JOB_MAX_ATTEMPTS, JOB_RETRY_SECONDS, JOBS_MAX_PENDING,
LLM_GLOBAL_DAILY_CAP, LLM_USER_DAILY_CAP, UPLOADS_ENABLED, ALLOWED_ORIGINS.
Local bootstrap publishes RESULTS_DIR (defaults bundled results). API PORT defaults 8000.
Frontend API_INTERNAL_URL is a server-side build setting, never a browser secret.
Compute: FREE_COMPUTE_ENABLED is a GitHub repository variable, DATABASE_URL is a GitHub secret.
BI_OUTPUT_DIR controls local CLI export path.

No Azure guide is supplied because Azure has not been deployed and tested.
