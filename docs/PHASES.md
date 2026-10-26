# Phase ledger

Master specification received 2026-10-26. Earlier foundation commits remain intact.

| Phase | Acceptance | Status |
|---|---|---|
| P0 | Compose starts web/API/Postgres, config/logging/health/CI | Passed locally: make up, all three containers healthy, 22 API tests |
| P1 | Migrated schema, seed, quarantined bad rows, DQ report | Passed: 27 tests; Postgres migration 0001; 24 parts; three quarantined rows |
| P2 | Segmentation, forecasts, rolling backtest, benchmark artifact | Passed: 32 tests, six models, 24 public series, held-out benchmark artifact |
| P3 | Simulation, policies, costs, sensitivity and statistical comparison | Passed: 37 tests; 10,000 draws/part; 648 grid cells; paired bootstrap; regression/NLP artifacts |
| P4 | Auth, role and object checks, audit, security tests | Passed: 43 tests; Argon2id, JWT, rotation/replay, CSRF, lockout, request caps and audit |
| P5 | Durable jobs, leases, retries, progress, cache, keyset pagination | Pending |
| P6 | Typed tools, guardrails, SSE, provider fallback | Pending |
| P7 | Pages, charts, accessibility and end-to-end smoke | Pending |
| P8 | Reports, results, measurements, docs and deploy guidance | Pending |
| P9 | Configuration validation, BOM, commonality, pooling | Pending (core) |

JD additions (regression, NLP, distribution fitting, finance, staging and BI)
are tracked within the related analytics, data, UI and documentation phases.
