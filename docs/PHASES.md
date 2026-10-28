# Phase ledger

Master specification received 2026-10-26. Earlier foundation commits remain intact.

| Phase | Acceptance | Status |
|---|---|---|
| P0 | Compose starts web/API/Postgres, config/logging/health/CI | Passed locally: make up, all three containers healthy, 22 API tests |
| P1 | Migrated schema, seed, quarantined bad rows, DQ report | Passed: 27 tests; Postgres migration 0001; 24 parts; three quarantined rows |
| P2 | Segmentation, forecasts, rolling backtest, benchmark artifact | Passed: 32 tests, six models, 24 public series, held-out benchmark artifact |
| P3 | Simulation, policies, costs, sensitivity and statistical comparison | Passed: 37 tests; 10,000 draws/part; 648 grid cells; paired bootstrap; regression/NLP artifacts |
| P4 | Auth, role and object checks, audit, security tests | Passed: 43 tests; Argon2id, JWT, rotation/replay, CSRF, lockout, request caps and audit |
| P5 | Durable jobs, leases, retries, progress, cache, keyset pagination | Implemented; ownership/retry/idle tests pass. Live PostgreSQL check: 10 jobs claimed uniquely across 4 threads and all fenced completions passed. |
| P6 | Typed tools, guardrails, SSE, provider fallback | Offline core implemented: 54 tests pass; external-provider chain and wall-clock tool deadlines remain pending |
| P7 | Pages, charts, accessibility and end-to-end smoke | Core workspace passes TypeScript build, 2 component tests and 1 Docker browser flow; axe found 0 violations on Configurations. Full page feature parity remains incomplete. |
| P8 | Reports, results, measurements, docs and deploy guidance | PDF endpoint tested and visually inspected; make results passes; local job/DB usage and Locust/Lighthouse measurements recorded. CI definitions added, remote execution/deployment unverified. |
| P9 | Configuration validation, BOM, commonality, pooling | Core implemented and tested: BOM cost/lead rollup, option validation and labeled theoretical pooling estimate |

JD additions (regression, NLP, distribution fitting, finance, staging and BI)
are tracked within the related analytics, data, UI and documentation phases.

## Continuation verification · 2026-10-26

- P1/JD staging: migration 0003 applied to local PostgreSQL; 24 inventory and 288 sales
  facts. Ten synthetic extract families and 11 CSV/Parquet exports covered by tests.
- P6/P7: browser consumes SSE events and displays cited tool traces; admin can inspect
  users, audit rows and the latest 100 jobs without timer polling.
- Verification: 61 backend tests passed, one dedicated-database test skipped; 2 frontend
  unit tests passed; TypeScript and production build passed; both Docker browser flows
  passed, with zero axe violations on the tested Configurations screen. Compose healthy.
- Separate PostgreSQL concurrency smoke passed earlier; SQL Server remains unverified.
- Follow-up validation: 74 backend tests passed, one dedicated-database test skipped.
  Synthetic extracts reject non-finite/negative numeric values, invalid months and duplicate
  fact keys before writing. Browser/axe/Lighthouse CI workflow added for public repositories;
  YAML parsed locally, remote execution not measured. Lighthouse login scores: performance
  0.97, accessibility 1.00, best practices 0.74 and SEO 1.00 (see results/ui.json).
- P9 option impact: read-only comparison endpoint and UI baseline selector calculate added/
  removed component quantities, cost differences and parallel-procurement lead differences.
  Invalid configurations omit impact values. Final suite: 76 backend tests passed, one
  dedicated-database test skipped; 2 frontend unit tests and 2 browser flows passed;
  TypeScript/build and Bandit medium/high scan passed; all Compose services healthy.

## Assistant scope and benchmark correction · 2026-10-26

- P6: segment scenarios now require an explicit ABC segment, filter returned parts and
  recompute totals. Ambiguous scopes, reversed history ranges and unsupported periods fail
  validation rather than silently returning broader results. Rejected calls are recorded
  without storing unvalidated arguments; session ownership violations generate audit events.
- P2: model-selection demand patterns now exclude validation/test observations. Previously
  full-history patterns could leak held-out information into grouping. Benchmark regenerated
  for all 24 series; per-model errors remain measured from the six held-out origins.
- Backend verification: 83 passed, one dedicated-database test skipped.
- Updated API rebuilt and healthy locally; both browser flows passed, with zero axe
  violations on Configurations. Frontend unit tests (2), TypeScript, production build and
  Bandit medium/high scan passed. No cloud deployment or external LLM calls were made.

## P7 Parts Explorer continuation · 2026-10-26

- Added server-side ABC segment filtering and ID sort direction. Cursor traversal tests
  verify exact membership, correct ordering and no duplicates in both directions.
- Added five browser-local named filter views with load/delete actions, bounded validation
  of stored settings and graceful handling of unavailable storage. Credentials are never saved.
- Pagination uses the applied view, so unapplied search edits cannot change the next page.
- Verification: 85 backend tests passed, one dedicated-database test skipped; 2 frontend
  tests passed; TypeScript and production build passed. Both browser flows passed, including
  saving/loading/deleting a view and pagination with unapplied edits. The initial browser
  failure was a dropdown test locator; corrected to use the accessible combobox role.
- Compose services healthy; Bandit medium/high scan passed. No paid services used.

## P4/P7 administrator access editing · 2026-10-26

- Existing non-managed users can have roles and disabled status changed in the Admin UI.
  Seeded demo/admin accounts are visibly protected and remain protected server-side.
- Access changes and before/after audit details now share a transaction. A simulated
  audit-write failure proves the access change rolls back. Integration coverage verifies
  viewer denial, protected accounts, old-token invalidation and disabled-account login denial.
- Verification: 86 backend tests passed, one dedicated-database test skipped; 2 frontend
  tests passed; TypeScript/build and Bandit medium/high passed; Compose healthy. Three
  browser tests passed: two live flows and one form test mocking only user endpoints.

## P2 interval calibration and service-hit evaluation · 2026-10-26

- Replaced final published rough interval ranges with per-horizon rolling residual quantiles,
  using only historical observations and at most 24 origins. Missing calibration is null.
- Added six-origin held-out one-step coverage, mean width and service-hit evaluation for
  each selected model/part. A target-spike test verifies calibration cannot see the target.
- Regenerated the 24-part benchmark and surfaced measured values in the Results UI.
  Service hit is forecast-bound coverage, explicitly distinguished from inventory fill rate.
- Verification: 89 backend tests passed, one dedicated-database test skipped; 2 frontend
  tests and 3 browser tests passed, including Results table visibility. TypeScript/build,
  Bandit medium/high scan and local Compose startup passed.
- GitHub destination is pending creation; all implementation commits are preserved locally.

## P1/JD purchase and BOM reverse imports · 2026-10-26

- Synthetic EKKO/EKPO and STKO/STPO extracts now transform back into purchase_orders and
  config_bom in the same transaction as the other generated warehouse facts. Monetary
  values, integer quantities, period/currency, headers and model/option relationships are
  validated before replacement. Demo contract: one detail per header, explicitly documented.
- Round-trip tests preserve original purchase prices, budgets, quantities and BOM exactly;
  invalid numeric values and relationships fail closed. No schema migration was required.
- Verification: 100 backend tests passed, one dedicated-database test skipped; three browser
  tests passed. Bandit medium/high passed. Updated API healthy; PostgreSQL contains 288
  purchase records and five BOM records following startup/import. Frontend unchanged.

## Saved-work continuation · 2026-10-27

- Resumed the two uncommitted configuration optimization files from the previous session.
  Component prices/leads now load in one joined query; SELECT count stays constant from
  two to 21 components. Missing component lead data produces a clear validation error.
- Backend suite: 102 passed, one dedicated-database test skipped. Bandit medium/high passed.
  Frontend unchanged; existing browser results apply to the preceding running build.
- Commit history and source backup are saved outside the repository as a Git bundle and
  source ZIP. These include committed code, tests, docs and run artifacts; ignored credentials,
  dependencies and live Docker database volumes are intentionally not exported.

## P0/P4 startup reliability · 2026-10-27

- Account initialization now handles competing inserts with savepoints, accepting only
  confirmed existing identities. Four independent Auth instances initialize and log in
  against one file-backed SQLite database with exactly two users and three roles.
- Production GET liveness probes allow internal HTTP; readiness and API routes retain
  HTTPS enforcement. A test rejects any database query during liveness checks.
- Backend suite: 104 passed, one dedicated-database test skipped; Bandit medium/high passed.
  Changes are committed and backed up. Running Docker images have not been rebuilt in this
  checkpoint; no new browser or live cloud verification is claimed.

## P6 local model routing and fallback · 2026-10-27

- Added optional development-only Ollama routing followed by deterministic Mock fallback.
  Default remains mock, zero daily call caps, no external model requests. Proposed read-only
  tool calls pass existing validation, ownership and role checks; answers remain cited
  deterministic summaries, with no untrusted model prose rendered.
- Added user-specific bounded caching, atomic in-process global/user daily attempt caps,
  bounded HTTP responses/timeouts, failure circuit cooldown and admin-only usage endpoint.
- Verification: 117 backend tests passed, one dedicated-database test skipped; Bandit
  medium/high passed. Focused assistant/provider tests passed after final metrics-label fix.
  No live model was called, cloud resources created or Docker images rebuilt this checkpoint.
- Gemini/compatible providers and persistent cross-process budgets remain unfinished.

## P6 persistent shared call budgets · 2026-10-27

- Migration 0004 adds UTC-day global and hashed-user counters. Atomic conditional updates
  reserve both counts in one transaction; exhausted user caps roll back the global increment.
  Missing/unavailable budget storage prevents model calls. Retention prunes old daily rows.
- Router uses shared counters whenever a database is configured; database-free standalone
  usage is explicitly labeled process-local. Mock default still makes no model calls.
- Verification: 120 backend tests passed, one dedicated-database test skipped; Bandit
  medium/high passed; updated Docker API healthy. Local PostgreSQL accepted exactly five
  of 24 attempts across eight workers at a cap of five, and a new instance read the persisted
  total. Evidence: results/llm_budget_postgres.json. SQL Server behavior remains unverified.


## P7 Policy Lab asynchronous job workflow · 2026-10-27

- Planners/admins can submit scenario jobs, manually refresh status/progress, and inspect
  completed results with the actual snapped grid settings. Retry/dead states are visible.
  Existing preview stays available. No automatic idle polling or fresh simulation is implied.
- One cryptographically random idempotency key is reused for each request's transport retries.
  Uses getRandomValues so offline HTTP works; browser testing caught and fixed randomUUID's
  secure-context restriction. New submissions create new keys. Job display is cleared at login/logout.
- Validation: 120 backend tests passed, one dedicated-database test skipped; two frontend
  tests and TypeScript passed; Docker production build passed and web is healthy.
  Four browser tests passed: two live flows (including real queued scenario completion),
  two mocked endpoint flows (user editing and failed-job/new-submission UI). Configurations
  axe scan reported zero violations; this does not establish application-wide accessibility.
- Still pending: baseline/optimized waterfall and broader chart coverage. Scenario state is
  session-local and a full browser reload loses the selected job; admins can use the job monitor.


## P7 scenario cost comparison and waterfall · 2026-10-27

- Preview and completed jobs show aggregated baseline/optimized holding, stockout and
  expedite costs, total annual cost, and savings. A floating-bar waterfall reconciles
  component changes to the optimized total. Capital investment remains separate.
- Native SVG uses an accessible title and an adjacent semantic table, with signed labels
  so direction does not depend on color. Invalid/missing costs show unavailable, not zero.
  Negative savings remain visible. No new dependencies or requests were added.
- React review: extracted component, derived values without effects, stable keys and unique
  accessible IDs, no shared mutable state. Unit tests cover multi-part reconciliation,
  negative savings, missing/non-finite/negative/string cost inputs.
- Verification: 120 backend passed, one dedicated-database test skipped; four frontend
  tests, TypeScript, production Docker build and four browser tests passed. Browser checks
  reconcile displayed totals against API annual costs and run axe on the comparison region
  (zero WCAG A/AA violations); this is not a full application accessibility certification.
- Other master-spec charts and model/integration gaps remain in HONEST_REPORT.md.


## P4 concurrent login lockout hardening · 2026-10-27

- Serialize account login decisions with a database write lock after password verification.
  Recheck current disabled/password/role state under that lock; failure counters and audit
  entries commit atomically. Concurrent failures cannot overwrite each other's counts.
- Active locks reject even valid passwords without extending the lock; expired locks start
  a new failure window and successful authentication clears failures. Unknown usernames
  retain dummy password verification and generic errors.
- Verification: 123 backend tests passed, one dedicated-database test skipped; Bandit
  medium/high passed; API image rebuilt healthy; four browser tests passed. New tests use
  independent Auth instances sharing SQLite, verify expiry/reset, and disable an account
  during password verification. The separate local PostgreSQL probe used eight concurrent
  attempts, reached the five-failure lock, and verified a valid password cannot bypass or
  extend it. Evidence: results/login_lockout_postgres.json. Synthetic probe account and
  counter removed after testing; redacted security audit entries retained.
- SQL Server runtime behavior remains unverified. Same-account decisions now serialize;
  broad login throughput has not been measured. Per-process request throttling remains.


## P6 local OpenAI-compatible protocol · 2026-10-27

- Added opt-in `openai-local,mock` against fixed loopback Ollama chat completions, using
  the existing explicit model setting. Default remains Mock with zero budgets. No cloud
  calls, API key discovery, model downloads or paid endpoints were used.
- Strict validated JSON routing, quota reservation, output limits, cooldown and fallback
  are shared with native Ollama. Empty choices and unavailable capabilities safely fall back.
- Verification: 15 provider tests passed with HTTP mocks; combined backend suite passed
  129 tests with two dedicated-database tests skipped. Bandit medium/high passed.
- Live model quality, Gemini/community providers and native capability negotiation remain.


## P8 SQL Server validation preparation · 2026-10-27

- Added offline compilation checks for every schema table, SQL Server queue locking hints,
  TOP pagination and the account write-lock statement. Both checks passed.
- SQL Server CI now pins Ubuntu 24.04 to match its ODBC package source, supports manual
  dispatch, and derives migration/test URLs from the same isolated database credentials.
  The prior independent URL secret could be absent or target the wrong database. CI now
  applies Alembic migrations before integration tests and includes atomic quota concurrency.
- The combined suite passed 129 tests; two dedicated-database integration tests skipped
  without TEST_DATABASE_URL. Offline compilation is not SQL Server runtime validation.
  This host is ARM64; no SQL Server instance was provisioned and no remote workflow ran.
  A public repository, opt-in variable and SQLSERVER_TEST_PASSWORD secret are still needed
  for the free GitHub-hosted x86 CI path. No paid infrastructure or billing enabled.


## P7 part forecast interval chart · 2026-10-27

- Part detail now charts future demand with a shaded lower/upper interval and an accessible
  table of all horizons. Values come directly from benchmark artifacts, with units and
  empirical-coverage caveats. Missing, mismatched, inverted or non-finite bounds are rejected.
- Component review: derived data outside effects, stable horizon keys, no new requests or
  dependencies, semantic table and labeled chart. Two additional frontend tests cover
  asymmetric interval alignment and invalid bounds.
- Six frontend tests, TypeScript and production Docker build passed. All four browser tests
  passed, including the real Part Detail interval section and its 12 forecast rows. Both
  local app containers are healthy. No claim of full chart accessibility certification.


## P6 guarded Gemini protocol and live local smoke · 2026-10-27

- Added opt-in Gemini JSON routing with header-only secret handling, explicit Flash model,
  operator free-tier confirmation, disabled uploads and existing quota/fallback controls.
  Only three app-authored public prompts may leave the machine; arbitrary input stays local.
  Default remains Mock. Multi-provider cascading and general cloud prompting remain pending.
- Protocol/security tests pass with simulated HTTP, including private input no-network,
  configuration rejection, empty/safety/incomplete responses and key representation isolation.
  Combined suite: 139 passed, two dedicated-database tests skipped; Bandit medium/high passed.
- Installed local Mistral was tested twice: both requests hit the five-second timeout and
  correctly fell back. Evidence records both failed attempts, not a successful model test.
  No live Gemini call, key retrieval, model download or paid service was used.


## P7 signed model-driver chart · 2026-10-27

- Part Detail renders signed TreeSHAP feature bars and an exact-value table, ordered by
  contribution magnitude. Base prediction is separate; negative contributions are preserved.
  Labels explicitly describe the fitted LightGBM model rather than attributing its drivers
  to a potentially different selected forecast. Missing/invalid artifacts are unavailable.
- Component review: derived data without effects, stable feature keys, existing chart library,
  semantic table, chart label, no added requests. Tests cover signed ordering, baseline
  exclusion and nonnumeric/non-finite rejection.
- Eight frontend tests, TypeScript, production Docker build and four browser tests passed;
  the real Part Detail test verifies eight feature rows. API and web containers healthy.
  Full backend: 139 passed, two dedicated-database tests skipped; Bandit medium/high passed.
- Simulation histogram, lead-time sensitivity and other unfinished charts remain pending.


## P7 simulation histogram and lead-time sensitivity · 2026-10-27

- Part Detail now displays the saved remaining-inventory-value histogram and three
  precomputed lead-time scenarios. API filters scenarios by part, service target and
  holding rate so only lead time changes; each scenario reoptimizes its stock policy.
- Tables show all bin counts, total draws, annual costs, stock and fill rate. Labels
  distinguish simulation counts from a time-series forecast and explain bin boundaries.
  Invalid bins, non-finite inputs and duplicate sensitivity points show unavailable.
- Validation: 140 backend tests passed, two dedicated-database tests skipped; 10 frontend
  tests, TypeScript, production builds and four browser tests passed. Browser verifies
  12 bins, 10,000 draws and three lead-time rows. Both app containers healthy.
- Live Gemini remains pending: the user confirmed billing disabled, but the repository
  root .env has no Gemini key/model and no alternative key file has been identified.
  No Gemini call or key retrieval occurred. GitHub is separately uncreated; local commits
  continue, while SQL Server remote runtime validation remains pending.


## P6/P8 reproducible live-validation preparation · 2026-10-27

- Added Gemini preflight with no network by default; explicit --live enables one capped
  app-authored public prompt. Environment input is parsed as data, never shell-executed.
  Sanitized output omits credentials and raw provider errors. Mock app settings stay intact.
- Actual local preflight: key, model and confirmation flag absent; zero requests attempted.
  User's verbal billing confirmation does not supply a key/model. Example environment now
  lists the settings without enabling them. LIVE_VALIDATION.md records remaining setup.
- SQL Server supported-host requirements verified against Microsoft: x86-64 Linux; this
  ARM64 Mac's emulation is unsupported. Existing gated x86 CI cannot run without a repository.
- Verification: 144 backend tests passed, two dedicated-database tests skipped; Bandit
  medium/high passed including the new script. New tests prove no-network preflight,
  one-attempt public prompt, literal environment parsing and secret-free failure output.
  No live Gemini or SQL Server result is claimed; frontend unchanged this checkpoint.


## GitHub creation and initial push · 2026-10-27

- Created private tulasiram2005/servicestock-ai in the authenticated user's account and
  pushed the existing main branch with complete Git history. No restart or history rewrite.
- Root .env remains ignored; only .env.example is tracked. Scanned 357 historical blobs
  for configured local secret values and common credential patterns; zero matches. This
  targeted scan is not a claim of exhaustive secret detection.
- Foundation/security CI jobs now share the public-repository gate already used by the
  other workflows, preventing hosted work on the new private repository. No billing or
  paid infrastructure enabled. SQL Server runtime CI remains pending by design.
- App code unchanged this checkpoint; preceding tests remain 144 backend passed/two
  skipped, 10 frontend passed and four browser passed. Remote CI is not claimed as passed.


## P6 assistant provider provenance correction · 2026-10-27

- Corrected provider labels: Gemini and OpenAI-compatible routing no longer incorrectly
  report Ollama. Gemini-configured responses no longer claim no external model was called,
  including when a failed external request may have preceded deterministic fallback.
- Verification: 148 backend tests passed, two dedicated-database tests skipped; new tests
  cover each provider and Gemini fallback. Bandit medium/high passed. No live cloud calls.


## P7 assistant copy and text export · 2026-10-27

- Added Copy answer and Download answer controls, including routing notice and source
  tool-call references. Exports omit hidden session identifiers and raw tool payloads.
  Clipboard denial/unavailability gives a usable download alternative. Text is exported
  as plain text, not executable HTML; transient object URLs are revoked.
- Verification: 11 frontend tests, TypeScript, production builds and four browser tests
  passed. Browser test downloads and reads the answer file, checks citations/assumptions,
  and verifies clipboard feedback. API, database and frontend containers healthy.
- Full backend suite: 148 passed, two dedicated-database tests skipped. Live Gemini and
  SQL Server validations remain pending; this update makes no external model calls.


## P2 multi-step held-out interval validation · 2026-10-27

- Extended validation to six forecast horizons with a separate observation count, coverage,
  mean interval width and service-bound hit rate per horizon. Forecast/calibration use only
  observations before issuance. Longer horizons without targets are explicitly unmeasured.
- Regenerated the 24-part benchmark; one-month coverage 0.9653 (144 observations), six-month
  coverage 0.9167 (24 observations). Overlapping sparse samples do not prove coverage or
  independence. Bounds concern demand in the target month, not cumulative lead-time demand.
- Results UI exposes 144 part/horizon rows; generated results documentation weights metrics
  by evaluated observations rather than assigning equal weight to different sample sizes.
- Validation: 150 backend tests passed, two database integration tests skipped; 11 frontend
  tests, TypeScript, production builds and four browser tests passed. Tests verify horizon
  counts, missing horizons, future-spike leakage protection and actual UI row count.
- Horizons beyond six months remain unvalidated with the current held-out window.


## P7 Data Quality rules and recorded history · 2026-10-27

- Data Quality now includes five rule categories and the latest 30 recorded runs in
  chronological order. Rule counts distinguish quarantined records from accepted outlier
  warnings. Labels disclose first-failure classification rather than implying independent
  per-rule pass rates. Quality score remains accepted rows / received rows.
- Chart appears only with multiple real runs; a single seed run explicitly lacks a trend.
  Empty database responses report unmeasured quality with no fabricated records.
- Verification: 152 backend passed, two database integration tests skipped; 11 frontend
  tests, TypeScript, production builds and four browser tests passed; Bandit medium/high
  passed. API tests cover authorization, 30-run limit/order, warnings and empty history.
  Browser verifies rule/history sections and the single-run explanation. Existing seed
  data remains unchanged; multiple synthetic runs were inserted only in isolated tests.


## P7 Overview ABC breakdown and opportunities · 2026-10-27

- Added ABC segment inventory chart and exact totals, plus ten opportunities ranked by
  annual simulated savings. Unmatched parts remain unclassified; negative financial values
  remain visible. Labels disclose synthetic business attributes.
- Verification: 153 backend tests passed, two dedicated-database integration tests skipped;
  11 frontend tests, TypeScript, production build and four browser tests passed. Added
  reconciliation/negative-value coverage and browser section/table assertions.
- SQL Server and live Gemini remain unvalidated; this is not full project completion.

## P6 Private Gemini setup · 2026-10-27

- Added hidden terminal input and exclusive owner-only secret-file creation. No key is
  accepted in command arguments or printed. Existing files and symlinks are not overwritten.
- Full backend suite: 155 passed, two dedicated-database integration tests skipped.
  New tests cover permissions, preservation, symlinks and dotenv injection rejection.
- User screenshot shows Free tier, but user confirms key is only copied, not locally saved.
  No live model request occurred. Browser remains disabled, preventing GitHub allowance check.

## P6 Live Gemini routing validation · 2026-10-27

- User privately configured key/model. Preflight passed and Git ignores the secret file.
- One live public KPI prompt passed in 1.603 seconds, selecting get_kpis. Recorded only
  sanitized evidence in results/gemini_live_smoke.json. This does not prove general quality.
- Setup now handles paste markers, gives redacted diagnostics, and preserves opaque
  punctuation without executing configuration as shell code.
- Full backend suite: 166 passed, two dedicated-database integration tests skipped.
- Mock remains the app default. SQL Server runtime validation is still pending.

## P0/P9 Portable refresh-token serialization · 2026-10-27

- Replaced SELECT FOR UPDATE reliance in refresh rotation with a row-locking no-op write
  before reading token state. SQL Server's SQLAlchemy dialect omits FOR UPDATE, so the
  old selection alone did not serialize competing rotations on that platform.
- Added a four-client concurrency test for local SQLite and the configured integration
  database. Exactly one rotation succeeds; replay revokes the entire replacement family.
- Full backend suite: 167 passed, three dedicated-database tests skipped. Separately ran
  the same four-attempt scenario against live local PostgreSQL: one success, family revoked.
  Evidence: results/refresh_rotation_postgres.json. Temporary probe accounts/tokens removed.
- Existing SQL Server workflow automatically includes the new configured-database case.
  SQL Server runtime remains unverified; browser access is disabled, blocking account
  allowance verification. No hosted workflow or paid service was enabled.

## SQL Server first hosted attempt · 2026-10-27

Run 40527320927 failed after 9m28s during database readiness. Container start, ODBC
installation and dependency installation succeeded; migrations and integration tests
were skipped. Logs exposed only "SQL Server did not become ready", so root cause remains
unknown. Added explicit IPv4 loopback, three-second login timeout, five-second query
timeout, twelve attempts, SQLSTATE-only errors and bounded container diagnostics with
password redaction. The remote fix is not yet validated. The $0 budget is unchanged.

## SQL Server second hosted attempt · 2026-10-27

Run 40533154602 on ac1a5e6 completed in 1m21s. Setup and migrations passed. Quota
concurrency and both refresh cases passed; job claims failed (three distinct claimed jobs
from ten immediate attempts). Changed the test to drain with bounded retries for transient
empty READPAST/SKIP LOCKED results. It still requires every enqueued ID exactly once and
successful fenced completion for every job. This interpretation needs another SQL Server
run; no runtime compatibility success is claimed. Evidence: results/sqlserver_runtime.json.

## P1/JD Multi-line synthetic detail mapping · 2026-10-27

Purchase and BOM transforms now preserve multiple numbered details per header, normalize
leading-zero line numbers, reject duplicates and ID collisions, and retain existing single-line
IDs. Verified totals, input-order independence and unchanged idempotent seeded ETL.
Targeted staging suite: 28 passed. Full backend suite recorded in current status report.
SQL Server run 40534000327 independently verified: four tests passed on f710f6b.
This import change has not been runtime-tested on SQL Server; physical staging schema and
external SAP integration are still unfinished.

## P5/JD Live zero-shot comparison · 2026-10-27

One explicitly enabled Gemini request classified 48 built-in synthetic comments, without
training examples or expected labels in the prompt. Macro-F1: Gemini 1.000, TF-IDF 0.667.
Only four unique held-out templates underlie the 48 rows; this is not production accuracy.
The measured artifact records predictions, model, timestamp, dataset hash and limitations.
Risk flags remain offline. Default invocation performs configuration preflight only.
The Results page now displays both scores with dataset limitations and missing-data handling.

Validation: 174 backend tests passed, three dedicated-database tests skipped; 13 frontend
unit tests passed; TypeScript and production build passed. All four browser tests passed
(two live flows and two mocked error/edit flows), including published comparison evidence.
Docker Compose services rebuilt and healthy. No new provider request was needed for these
tests. Historical targeted SQL Server success remains separate from this local test suite.

## P6 Ordered provider fallback · 2026-10-27

Configured Gemini, local OpenAI-compatible, and native Ollama adapters now form an
ordered chain ending with Mock. Shared attempt budgets, provider-specific cooldowns,
provider/user cache separation and request-context provenance prevent cap bypass and
incorrect provider attribution. Gemini's public-only input gate remains in every chain.
Admin capability observations distinguish unprobed, validated JSON plans and unavailable
responses. Native tool negotiation and arbitrary community endpoints remain unfinished.
Full backend validation: 183 passed, three dedicated-database cases skipped. Mock HTTP
tests include 429 degradation, third-adapter success, cap exhaustion, private input
protection and response labels. No live model request or billing change was made.
Frontend and browser checks were not rerun: this phase changes backend routing only.

## P1/JD Physical synthetic staging · 2026-10-27

Migration 0005 adds ten typed SAP-style tables in `staging` on PostgreSQL/SQL Server.
SQLite maps this namespace to main. Legacy JSON history remains untouched by migration;
the next synthetic ETL populates typed landing tables, reads them to transform warehouse
facts, and commits all changes together. Decimal prices, source field names and synthetic
labels are preserved. Failed transforms roll back staged and warehouse replacements.

185 backend tests passed; three dedicated-database cases skipped. SQLite existing-data
upgrade/downgrade/re-upgrade preserves legacy history. SQL Server DDL compiles. Local
PostgreSQL upgraded to 0005 with ten physical tables and 1,258 rows; two successive ETL
runs were identical. New staging SQL Server runtime validation remains outstanding.
All four browser checks passed against the updated local stack (two live application
flows and two mocked error/edit flows). No external model or paid service was used.

## P7/P8 Broader accessibility checks · 2026-10-28

Added automated axe scans across Overview, Parts, Policy Lab, Data Quality, Assistant,
Configurations, Results, Reports and Admin in dark and light themes. The first scan
found low contrast in light-theme workspace labels and footer text; both now use the
theme's readable muted color. Rerun: 18 scans, zero automated violations.
Five browser tests passed against the local stack. Frontend unit suite (13 tests),
TypeScript and production build passed during the implementation of this change.
No backend code changed; the previous backend result remains 185 passed, three skipped.
The browser workflow now preserves the accessibility evidence artifact. Its existing
private-repository guard is unchanged. This is not manual accessibility certification
and does not cover all interactive states, mobile layouts or screen readers.

## P8 Expanded database and security validation · 2026-10-28

Added a seeded application smoke for SQLite and an explicitly configured empty disposable
database, including physical staging, repeated ETL, published results, authentication,
viewer/admin restrictions, configuration impact and job ownership. Existing application
data is rejected before seeding. The manual SQL Server workflow now runs this check before
the concurrency suite. Its new SQL Server execution remains outstanding.

Local full suite: 186 passed, four environment-dependent cases skipped. On an isolated
PostgreSQL database migrated to 0005: six application/concurrency tests passed; temporary
database removed. Runtime pip-audit and npm audit: zero known vulnerabilities. Bandit
medium/high: zero findings. No billing or paid infrastructure enabled.

## P8 Bounded local performance measurement · 2026-10-28

The local-only Locust runner now accepts bounded user/duration settings (1–10 users,
10–60 seconds), defaults to five users for 30 seconds, stops users on failed login,
and writes results atomically. Evidence includes requested concurrency, duration,
HTTP status counts and per-endpoint latency instead of the shutdown-time active count.
Five users ramped at one per second against the unchanged local stack: 61 requests,
zero failures, 29 ms p50, 53 ms p95, approximately 2.12 requests/second. All responses
were HTTP 200. Routes: login, parts and KPIs. This shared-account, short read workload
is not saturation testing, production capacity, or deployed latency evidence.
Scripts compile and the actual bounded run exited successfully. No app code changed.

## Expanded hosted SQL Server verification · 2026-10-28

[Run 40618520967](https://github.com/tulasiram2005/servicestock-ai/actions/runs/40618520967)
on 1360bc0 succeeded in 1m6s. Migration 0005, typed staging import, seeded application
authenticated reads, access restrictions, configuration impact and job ownership passed.
Logs show 2 application tests plus 4 concurrency tests passed (two cases are SQLite).
The isolated SQL Server container was removed successfully. This supersedes pending
new-staging runtime status; it does not certify every application path.
Before dispatch, account UI showed 14/3,000 included minutes, 0/2 GB storage, $0 billable
usage and the existing $0 Actions budget. No billing or repository visibility changed.
Nonblocking Node action-runtime and TestClient deprecation warnings remain.

## P7 Keyboard navigation · 2026-10-28

Added Skip to content as the first keyboard target, with visible focus styling and
focusable login/workspace content. Browser-driven keyboard checks verify Tab order,
Enter activation, mouse-free sign-in and navigation bypass after authentication.
Six browser tests, 13 frontend unit tests, TypeScript and production build passed.
Eighteen axe scans remain free of automated violations. Human screen-reader testing
and comprehensive manual accessibility evaluation remain outstanding.
