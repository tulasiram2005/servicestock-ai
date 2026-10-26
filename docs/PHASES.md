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
