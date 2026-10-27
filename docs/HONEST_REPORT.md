# Implementation and testing status

This is an implemented local demonstration, not full master-spec completion or a production deployment.

Built: Compose startup, portable schema and migrations, public demand cache with provenance,
DQ quarantine, six-model backtests, TreeSHAP, simulation/cost/grid artifacts, synthetic delay
regression and comment classification, finance summaries, JWT/Argon2/refresh/CSRF controls,
leased jobs, typed offline assistant, SSE, connected workspace, configuration BOM/pooling,
on-demand PDF endpoint and CLI BI export code.

Latest local continuation (2026-10-27): ten synthetic extract families, inventory/sales
warehouse migration, 11 CSV/Parquet exports, numeric/reference validation, streamed UI
tool traces, manual administrator job monitor and configuration option impact comparison.
185 backend tests passed (three dedicated-database tests skipped), 13 frontend unit tests and
4 browser tests passed (two live flows, plus mocked user-edit and failed-job UI checks).
TypeScript, production build and Bandit medium/high scan passed.
Local Compose services are healthy. These checks do not establish full master-spec completion.

Assistant scope checks now prevent silently broadening segment or period requests, and
rejected calls are logged without unvalidated arguments. Forecast selection patterns are
frozen before validation/test observations; benchmark artifacts were regenerated after
correcting the earlier use of full-history patterns for model-selection grouping.

Evidence: phase tests are recorded in docs/PHASES.md; browser smoke and axe results in results/ui.json.
Results are regenerated with make results. Local runtime metrics are separate from cloud metrics.

Remaining master-spec gaps:
- Development-only native Ollama and local OpenAI-compatible routing with Mock fallback,
  persistent shared-database daily caps,
  bounded response reads, user-isolated caching and failure cooldown is implemented and
  tested with simulated HTTP responses. Two live local Mistral attempts timed out and fell
  back; successful model quality is unmeasured. An opt-in Gemini adapter is implemented
  for three app-authored public prompts and tested with simulated responses, and a live public KPI routing check passed. Free-tier status is based on the user
  screenshot and confirmation; billing was not verified through a provider API. Community adapters, general cloud
  prompting, native-tool capability negotiation, token/cost accounting and tool deadlines
  remain pending. Ordered fallback across the configured adapters and observed JSON-plan
  capability reporting are implemented; native tool calling remains disabled.
  See LLM_PROVIDERS.md for settings and exact limitations.
- One live Gemini zero-shot NLP comparison is now measured: macro-F1 1.00 versus
  offline TF-IDF 0.667, on 48 synthetic rows derived from only four held-out phrase
  templates. This is not independent real-world accuracy evidence. Risk flags still use
  the offline baseline. See results/nlp_comparison.json. Forecast intervals use per-horizon
  rolling residual calibration; one- through six-month coverage, width and service hit rate
  are measured within six held-out periods, with decreasing per-horizon sample counts.
  Coverage is empirical, not guaranteed; horizons beyond six months remain unvalidated.
- Ten synthetic extract families now support inventory/sales and purchase/BOM reverse ETL,
  with 11 CSV/Parquet export tables including KPIs/finance. Ten typed tables now use a physical staging schema on PostgreSQL/SQL Server,
  with a SQLite namespace mapping. Local PostgreSQL migration and ETL passed; new staging
  SQL Server runtime validation and general external SAP integration remain outstanding. Purchase and BOM transforms now accept
  multiple numbered details per header, reject duplicate lines, and preserve legacy IDs.
- Parts Explorer now supports server-side ABC filters, ascending/descending ID order,
  cursor pagination, and five browser-local saved filter views. Saved views are shared by
  users of the browser, contain no credentials, and are not synchronized between devices.
- Admin role/disabled editing is implemented for existing non-environment-managed accounts.
  Role changes and their audit entries are atomic; rollback on audit failure is tested.
  Creating new accounts through the UI is not implemented.
- Policy Lab now submits jobs for planners/admins, displays manually refreshed progress and
  errors, and renders completed precomputed-grid results. Local HTTP submission and a real
  worker completion were verified. Selected job state is session-local.
- Policy Lab includes baseline/optimized cost tables and a component waterfall for previews
  and completed jobs. Displayed totals were checked against API results; missing cost inputs
  show unavailable. Part Detail now renders forecast intervals with a shaded band and
  exact-value table, signed LightGBM TreeSHAP driver bars, a simulation histogram and
  lead-time sensitivity at fixed service/holding settings. Other detailed frontend charts
  remain missing, along with
  optimistic feedback. The UI consumes SSE tool/answer events and
  provides a manual-refresh administrator job monitor; the server computes tools before
  emitting events, so this is not incremental model-token streaming.
- Local Bandit medium/high scan and runtime pip-audit pass after upgrading PyJWT. Lighthouse
  and a short local Locust smoke are measured; full load capacity is not. CI security and SQL Server
  workflow definitions exist; SQL Server schema/lock statements compile offline and its workflow
  now runs migrations and derives its isolated connection settings, with targeted SQL Server runtime checks now passing (four workflow tests). Full
  application coverage on SQL Server and all remote quality gates remain unverified.
- Concurrent account-seeding conflict handling is implemented and tested with independent
  instances against shared SQLite; account-seeding PostgreSQL/SQL Server validation remains.
  Concurrent login lockout is now serialized and tested with shared SQLite and live local
  PostgreSQL (eight simultaneous failures). SQL Server lockout runtime remains unverified.
  External worker notifications, fully enforced audit privileges,
  provider-specific quotas and deployment wake-up behavior need further validation.
- No live deployment, paid service, billing enablement or no-card account verification occurred.
- GitHub repository https://github.com/tulasiram2005/servicestock-ai was created private
  on 2026-10-27 and the existing main history pushed. Most hosted CI jobs remain gated off for private repositories. A manually triggered
  SQL Server run passed within the included allowance with the existing $0 budget unchanged.

The local source subset is 24 series. All costs, lead times and business attributes are synthetic.
Negative capital freed is retained honestly. Pooling is theoretical, not empirical stock savings.

Live-check setup and platform constraints: see LIVE_VALIDATION.md. Gemini preflight is
implemented and tested. One live Gemini KPI routing request passed in 1.603 seconds using
the private `.env.gemini` file; see results/gemini_live_smoke.json. General model quality
is not established, and application defaults remain offline.

Assistant Copy answer and plain-text download now include routing notices and source
references; verified in browser. Gemini/local provider provenance labels were corrected.

Data Quality includes rule counts and a bounded 30-run history, with a trend only when
multiple recorded runs exist. The seeded local demonstration currently has one run.

Overview now includes ABC inventory totals and ten ranked simulated savings opportunities,
with exact tables and negative savings/capital retained. Reconciliation tests and browser
checks pass. Private Actions allowance and the $0 budget were verified; public visibility is
not required for the successful manual test. See LIVE_VALIDATION.md.

Refresh rotation now serializes with a portable no-op write. Concurrent one-use/replay
behavior passed SQLite and live PostgreSQL checks; the targeted SQL Server concurrency test also passed.
