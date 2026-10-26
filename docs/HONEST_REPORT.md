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
117 backend tests passed (one dedicated-database test skipped), 2 frontend unit tests and
3 browser tests passed (two live flows plus a user-edit form test with mocked user endpoints).
TypeScript, production build and Bandit medium/high scan passed.
Local Compose services are healthy. These checks do not establish full master-spec completion.

Assistant scope checks now prevent silently broadening segment or period requests, and
rejected calls are logged without unvalidated arguments. Forecast selection patterns are
frozen before validation/test observations; benchmark artifacts were regenerated after
correcting the earlier use of full-history patterns for model-selection grouping.

Evidence: phase tests are recorded in docs/PHASES.md; browser smoke and axe results in results/ui.json.
Results are regenerated with make results. Local runtime metrics are separate from cloud metrics.

Remaining master-spec gaps:
- Development-only local Ollama routing with Mock fallback, per-process daily caps,
  bounded response reads, user-isolated caching and failure cooldown is implemented and
  tested with simulated HTTP responses. Live model quality is unmeasured. External Gemini/
  compatible adapters, capability detection, distributed daily quotas and per-tool deadlines
  remain pending. See LLM_PROVIDERS.md for settings and exact limitations.
- Transformer/zero-shot NLP comparison remains. Forecast intervals now use per-horizon
  rolling residual calibration; one-step coverage, interval width and service hit rate are
  measured over six held-out origins per part. Coverage is empirical, not guaranteed;
  multi-step coverage validation remains outstanding.
- Ten synthetic extract families now support inventory/sales and purchase/BOM reverse ETL,
  with 11 CSV/Parquet export tables including KPIs/finance. A physical staging schema and
  general multi-line external SAP mapping remain missing. The current synthetic contract
  deliberately accepts one detail per header and rejects duplicate details.
- Parts Explorer now supports server-side ABC filters, ascending/descending ID order,
  cursor pagination, and five browser-local saved filter views. Saved views are shared by
  users of the browser, contain no credentials, and are not synchronized between devices.
- Admin role/disabled editing is implemented for existing non-environment-managed accounts.
  Role changes and their audit entries are atomic; rollback on audit failure is tested.
  Creating new accounts through the UI is not implemented.
- Detailed frontend features still missing include full charts/waterfalls and
  optimistic feedback. The UI consumes SSE tool/answer events and
  provides a manual-refresh administrator job monitor; the server computes tools before
  emitting events, so this is not incremental model-token streaming.
- Local Bandit medium/high scan and runtime pip-audit pass after upgrading PyJWT. Lighthouse
  and a short local Locust smoke are measured; full load capacity is not. CI security and SQL Server
  workflow definitions exist but remote runs remain unverified; no claim that all gates pass.
- Concurrent account-seeding conflict handling is implemented and tested with independent
  instances against shared SQLite; PostgreSQL/SQL Server validation and concurrent lockout
  hardening remain. External worker notifications, fully enforced audit privileges,
  provider quotas and deployment wake-up behavior need further validation.
- No live deployment, paid service, billing enablement or no-card account verification occurred.
- GitHub access was checked; no ServiceStock remote exists and the user confirmed no repository
  has been created. All commits remain local; nothing has been pushed to GitHub.

The local source subset is 24 series. All costs, lead times and business attributes are synthetic.
Negative capital freed is retained honestly. Pooling is theoretical, not empirical stock savings.
