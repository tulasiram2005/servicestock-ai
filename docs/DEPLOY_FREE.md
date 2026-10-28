# Free deployment guide (not deployed or verified end-to-end)

Local Docker is the verified default: make up. Read generated .env locally for credentials.
Do not paste secrets into chat or GitHub. Production deployment remains gated on security
review and account-specific no-card eligibility; this document is setup guidance, not evidence
of deployment.

1. Keep the existing GitHub repository private. Do not change visibility for deployment.
   Standard Linux Actions can use verified included private-repository minutes; leave
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
5. Gemini is implemented and live-tested for restricted public prompts; leave
   LLM_PROVIDER_ORDER=mock and both daily caps zero for the initial deployment.
   Enable Gemini separately only with verified free model/account eligibility and disabled billing.
6. Existing heavy-compute workflows remain public-only gated. Do not make this repository
   public merely to enable them. Changing those guards requires a separately verified allowance.
   Configure optional GitHub DATABASE_URL secret for compact result publishing only after
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

## Verification checkpoint · 2026-10-28

Provider documentation was rechecked; see FREE_TIER_BUDGET.md. This does not verify
account eligibility, connection permissions or a deployed application. No Render/Neon
resource has been provisioned or confirmed for this project. A Vercel-only frontend
without its backend/database would not complete deployment.

Production startup deliberately does not migrate or seed. Complete migrations through
0005, synthetic seeding/typed ETL, and result publication in a trusted environment before
starting the API. Never point validation scripts at a production database: the application
integration test requires an empty disposable database. Verify TLS and explicit HTTPS
origins; duplicate/conflicting sslmode values are rejected by application configuration.
Stop if any provider asks for a card, paid upgrade or unavailable free quota. Never add
a pinger to avoid idle suspension. Record real deployed smoke results before changing
this document's undeployed status.

## Account discovery — 2026-10-28

Read-only connected-account checks confirmed the Neon organization is on its free plan.
Its two existing projects are unrelated to ServiceStock; no database was created or reused.
The user selected Render “My Workspace”. It contains three existing free web services
and no ServiceStock service. The listing does not establish remaining shared instance
hours, payment-method state or overage protection. Verify those before provisioning.
No existing services, billing settings or repository visibility were changed.

## Hosted preparation — 2026-10-28

Render dashboard verification: Hobby, no card on file, $0 pipeline spend limit and
$0 accrued charges. At inspection, usage was 24.77/750 instance hours, 51/500 pipeline
minutes and 16 MB/5 GB bandwidth. These are time-specific shared-workspace readings.

Created dedicated Neon Free project `old-dust-65610326` (servicestock-ai), PostgreSQL 16,
AWS us-west-2, fixed 0.25 CU, requested logical storage quota 500,000,000 bytes.
Custom suspension timeout was rejected by the Free account; creation succeeded with
account-managed defaults. The returned configuration's zero timeout is not proof of
actual idle behavior; verify scale-to-zero in the console before declaring it tested.
Migrations reached 0005 and 24 seeded parts were read back through pooled TLS access.
Staging and result publication remain in progress at this checkpoint.

Hosted credentials are stored only in ignored, owner-readable `.env.hosted`. Never
print this file or include it in commits/backups. No Render service or Vercel project
has been created. Vercel team access was approved, but plan eligibility is not yet
verified. Browser access became disabled again during the check. Render/Neon connectors
are no longer available in this session. Do not bypass access or secret-output blocks.
