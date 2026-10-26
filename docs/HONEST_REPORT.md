# Implementation and testing status

This is an implemented local demonstration, not full master-spec completion or a production deployment.

Built: Compose startup, portable schema and migrations, public demand cache with provenance,
DQ quarantine, six-model backtests, TreeSHAP, simulation/cost/grid artifacts, synthetic delay
regression and comment classification, finance summaries, JWT/Argon2/refresh/CSRF controls,
leased jobs, typed offline assistant, SSE, connected workspace, configuration BOM/pooling,
on-demand PDF endpoint and CLI BI export code.

Latest local continuation (2026-10-26): ten synthetic extract families, inventory/sales
warehouse migration, 11 CSV/Parquet exports, numeric/reference validation, streamed UI
tool traces, manual administrator job monitor and configuration option impact comparison.
83 backend tests passed (one dedicated-database test skipped), 2 frontend unit tests and
2 browser flows passed. TypeScript, production build and Bandit medium/high scan passed.
Local Compose services are healthy. These checks do not establish full master-spec completion.

Assistant scope checks now prevent silently broadening segment or period requests, and
rejected calls are logged without unvalidated arguments. Forecast selection patterns are
frozen before validation/test observations; benchmark artifacts were regenerated after
correcting the earlier use of full-history patterns for model-selection grouping.

Evidence: phase tests are recorded in docs/PHASES.md; browser smoke and axe results in results/ui.json.
Results are regenerated with make results. Local runtime metrics are separate from cloud metrics.

Remaining master-spec gaps:
- Optional external LLM chain, capability detection, distributed daily quotas and per-tool deadlines.
- Transformer/zero-shot NLP comparison; calibrated forecast intervals and service-level backtest metric.
- Physical staging schema and reverse purchase/BOM ETL: ten synthetic extract families now
  exist, with inventory/sales ETL and 11 CSV/Parquet export tables including KPIs/finance.
- Detailed frontend features still missing include saved views, full charts/waterfalls,
  optimistic feedback and user role editing. The UI consumes SSE tool/answer events and
  provides a manual-refresh administrator job monitor; the server computes tools before
  emitting events, so this is not incremental model-token streaming.
- Local Bandit medium/high scan and runtime pip-audit pass after upgrading PyJWT. Lighthouse
  and a short local Locust smoke are measured; full load capacity is not. CI security and SQL Server
  workflow definitions exist but remote runs remain unverified; no claim that all gates pass.
- Multi-process safe login seeding, external worker notifications, fully enforced audit privileges,
  provider quotas and deployment wake-up behavior need further validation.
- No live deployment, paid service, billing enablement or no-card account verification occurred.

The local source subset is 24 series. All costs, lead times and business attributes are synthetic.
Negative capital freed is retained honestly. Pooling is theoretical, not empirical stock savings.
