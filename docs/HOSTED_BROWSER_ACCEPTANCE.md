# Hosted browser acceptance — 2026-10-28

Target: https://servicestock-ai.vercel.app (frontend deployment 6eec595;
backend a9ca299). Tests used the approved read-only demo account. Credentials,
cookies and tokens are excluded from this record.

Observed passes across the resumed browser sessions:
- Sign-in reaches the viewer dashboard; loading feedback is visible while waiting.
- Parts list loads; P0001 opens demand, forecast, policy and sensitivity sections.
- Policy Lab default comparison returns the nearest grid settings and a 24-part
  annual cost comparison: baseline $1,729.50, optimized $1,308.41.
- Data Quality loads 1,227 received rows, 1,224 accepted and three quarantined.
- Default AC configuration validates and returns P0001/P0002 components.
- Results renders forecast and measured zero-shot comparison sections.
- Assistant returns a deterministic KPI summary with its tool-call citation
  and explicitly says no external model was called.
- Reports correctly denies exports to the viewer account.
- Sign-out returns to empty login fields and removes workspace content.

Theme toggle was exercised; complete contrast and persistence checks were not
performed in this hosted session. No full keyboard traversal, responsive viewport
matrix, planner/admin exports, option-change permutations, or human screen-reader
listening test was completed. These observations do not certify every user journey
or WCAG compliance. See SCREEN_READER_ACCEPTANCE.md for the human acceptance sheet.
Screenshots are retained outside the repository in the task outputs folder:
hosted-assistant-verified.png and hosted-reports-viewer.png.
