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
153 backend tests passed (two dedicated-database tests skipped), 11 frontend unit tests and
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
  for three app-authored public prompts and tested with simulated responses, but no live
  Gemini call or account/billing verification occurred. Community adapters, general cloud
  prompting, provider cascading, capability detection, token/cost accounting and tool deadlines
  remain pending. See LLM_PROVIDERS.md for settings and exact limitations.
- Transformer/zero-shot NLP comparison remains. Forecast intervals now use per-horizon
  rolling residual calibration; one- through six-month coverage, width and service hit rate
  are measured within six held-out periods, with decreasing per-horizon sample counts.
  Coverage is empirical, not guaranteed; horizons beyond six months remain unvalidated.
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
  now runs migrations and derives its isolated connection settings, but runtime and remote runs remain unverified; no claim that all gates pass.
- Concurrent account-seeding conflict handling is implemented and tested with independent
  instances against shared SQLite; account-seeding PostgreSQL/SQL Server validation remains.
  Concurrent login lockout is now serialized and tested with shared SQLite and live local
  PostgreSQL (eight simultaneous failures). SQL Server lockout runtime remains unverified.
  External worker notifications, fully enforced audit privileges,
  provider-specific quotas and deployment wake-up behavior need further validation.
- No live deployment, paid service, billing enablement or no-card account verification occurred.
- GitHub repository https://github.com/tulasiram2005/servicestock-ai was created private
  on 2026-10-27 and the existing main history pushed. Hosted CI jobs are gated off for
  private repositories to preserve free-only operation; remote checks remain unrun.

The local source subset is 24 series. All costs, lead times and business attributes are synthetic.
Negative capital freed is retained honestly. Pooling is theoretical, not empirical stock savings.

Live-check setup and platform constraints: see LIVE_VALIDATION.md. Gemini preflight is
implemented and tested; the root environment still has no key/model, so zero calls were made.

Assistant Copy answer and plain-text download now include routing notices and source
references; verified in browser. Gemini/local provider provenance labels were corrected.

Data Quality includes rule counts and a bounded 30-run history, with a trend only when
multiple recorded runs exist. The seeded local demonstration currently has one run.

Overview now includes ABC inventory totals and ten ranked simulated savings opportunities,
with exact tables and negative savings/capital retained. Reconciliation tests and browser
checks pass. Private Actions eligibility needs account verification; public visibility is
not a requirement imposed by GitHub. See LIVE_VALIDATION.md.
