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
