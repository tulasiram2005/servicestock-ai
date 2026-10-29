# Hosted viewer checks — 2026-10-29

Render deployment dep-dbhhi3vb9u1s739s9jc0 is live at commit
 ae87e6bca190682f74bdb845b4a8872ef49df39c. This confirms the guarded Groq
adapter code is deployed; it remains unconfigured and disabled.

Checked through the real browser at https://servicestock-ai.vercel.app using
the approved demo credentials, without displaying or saving credentials:

- Login reached viewer overview with inventory USD 6,226.
- Assistant returned KPI data with a trace ID and explicitly stated offline
  default / no external model called. Answer download completed.
- Parts list loaded; Open P0001 loaded forecast diagnostics, signed TreeSHAP
  table, 10,000-draw simulation table and lead-time sensitivity table.
- Policy Lab comparison returned per-part savings, including negative values.
- Default AC configuration validated and returned a USD 73 component total.
- Results loaded persisted interval measurements and limitations.
- Data Quality displayed 1,227 received, 1,224 accepted, 3 quarantined rows.
- Reports correctly explained that viewer accounts cannot export review packs.
- Enter activated Overview navigation. Sign-out returned the login form.

Screenshot: ../.. /hosted-viewer-verified.png (task outputs directory).

These checks cover the hosted viewer paths above. They do not establish full
admin mutation/export coverage, responsive coverage at every viewport, live
remote-provider behavior, or human screen-reader acceptance. The previous local
suite separately passed 7 browser tests and 18 automated accessibility scans.

No paid plan, billing setting, provider key, or remote-model configuration changed.
