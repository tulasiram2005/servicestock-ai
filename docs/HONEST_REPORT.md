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
221 backend tests passed (four dedicated-database tests skipped), 13 frontend unit tests and
6 browser tests passed (two live flows, mocked user-edit and failed-job UI checks,
and automated accessibility scans of nine initial admin workspace views in both themes).
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
  prompting, native-tool capability negotiation, durable token budgets/cost accounting and tool deadlines
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
  with a SQLite namespace mapping. Local PostgreSQL migration and ETL passed; expanded hosted SQL Server staging/application
  smoke also passed (run 40618520967). General external SAP integration remains outstanding. Purchase and BOM transforms now accept
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

Accessibility continuation (2026-10-28): fixed light-theme workspace-label and footer
contrast. Eighteen axe scans (nine initial admin views × two themes) report zero
WCAG 2 A/AA and 2.1 AA automated violations. These are automated checks only; manual
keyboard/screen-reader evaluation, mobile layouts and all interactive states remain
outside this result. Evidence: results/accessibility.json. All five browser tests passed.

Broader database/security continuation (2026-10-28): disposable PostgreSQL migrations,
seeded application/staging and concurrency checks passed (six tests including two SQLite
cases). The test covers authenticated data endpoints, viewer/admin restrictions, job
ownership and typed staging ETL. The temporary database was removed. The expanded SQL
Server workflow includes this application test before concurrency checks, but has not
yet been run. Python runtime dependency audit and npm audit reported zero known
vulnerabilities; Bandit reported zero medium/high findings. These tools do not establish
absence of vulnerabilities, production load capacity or complete SQL Server support.

Performance continuation (2026-10-28): a five-user, 30-second local Locust read
workload completed 61 requests with zero failures and 53 ms p95 latency. HTTP status
and endpoint breakdowns are recorded in results/load.json. Existing rate limits were
unchanged. Sustained capacity, mixed writes and deployed latency remain unmeasured.

Hosted SQL Server update (2026-10-28): run 40618520967 on 1360bc0 passed migrations
through 0005, two seeded application/staging cases and four concurrency cases in 66
seconds (four SQL Server cases and two SQLite cases overall). This supersedes earlier
statements that the new staging/application smoke remains unrun. The temporary container
was removed. Included allowance and the unchanged $0 budget were verified beforehand.
The smoke covers selected paths, not all application behavior or production certification.
Remaining work includes manual accessibility, advanced provider features and deployment
verification; sustained production capacity remains unmeasured.

Keyboard accessibility continuation (2026-10-28): added a visible-on-focus skip link
and focusable content targets on login/workspace views. Browser keyboard input verified
Tab order, Enter activation, sign-in without a mouse and bypassing repeated navigation.
All six browser tests passed; the 18 theme/page axe scans still show zero violations.
This is browser-driven keyboard testing, not a human screen-reader audit.

Provider accounting continuation (2026-10-28): admin usage includes provider-reported
token observations with per-field completeness counts. Missing data is not zero; cached
routes do not double-count, and invalid plans retain reported usage. These are process-
lifetime observations, not durable token budgets or billing reconciliation. Cost remains
unmeasured. Full backend suite: 197 passed, four database-dependent cases skipped.

Deployment safeguards (2026-10-28): production configuration now rejects ambiguous or
misleading TLS parameters and malformed HTTPS origins. Sixteen regression cases cover
these guards. Full backend suite: 213 passed, four dedicated-database cases skipped.
Deployment instructions retain private GitHub visibility and distinguish free-tier
documentation from account eligibility. No hosted application has been verified.

Provider admission (2026-10-28): configurable process-local concurrency of 1–4
(default 1) bounds simultaneous provider chains. Busy requests fall back without spending
a model attempt. Eight new cases cover admission, release after unexpected exceptions,
configuration and environment parsing. Full suite: 221 passed, four skipped. Human
screen-reader acceptance is prepared in SCREEN_READER_ACCEPTANCE.md, but not performed.
Render billing/allowance verification is blocked by disabled browser access; no resources
were provisioned and no paid services enabled.

Provider backoff continuation (2026-10-28): Retry-After seconds and HTTP dates are
honored within a 60-second to one-hour cooldown. Repeated failures use exponential
backoff; a validated response resets the failure count. Cooldown requests immediately
fall through without spending another attempt. Admin usage exposes remaining cooldown
seconds without error payloads or secrets. This is not automatic retry or native tool
negotiation. Community adapters, durable token budgets and native-tool negotiation remain
unfinished. Hosted HTTP verification is recorded in DEPLOY_FREE.md and hosted_smoke.json;
human screen-reader acceptance and full hosted browser journeys remain unverified.
