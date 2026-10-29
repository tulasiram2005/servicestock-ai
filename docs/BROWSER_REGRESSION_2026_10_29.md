# Browser regression — 2026-10-29

The macOS Chromium launch restriction was resolved for testing by using the existing
local mcr.microsoft.com/playwright:v1.64.1-noble Docker image, with an isolated
node_modules volume. No hosted runner or paid infrastructure was used.

The first working suite ran six functional journeys successfully and found two
accessibility issues: light-theme navigation markers had insufficient contrast,
and an overflowing Results table was not keyboard focusable. Marker opacity is
now 1 and generic data-table scroll regions are labelled, focusable and visibly
outlined on keyboard focus. The production build and 13 frontend unit tests pass.

The suite covers keyboard login/skip link, three responsive widths, part drilldown,
scenario/assistant/configuration, admin jobs, plus mocked role editing and job-error
handling. The role-editing and job-error cases are intentionally mocked; they do
not establish a full hosted admin test. Automated accessibility scans cover nine
initial admin views in two themes, not every interaction or human screen-reader use.

Machine-readable latest results: results/accessibility.json and results/ui.json.

Final rerun: all 7 browser tests passed in 12.5 seconds. All 18 automated
accessibility page/theme checks reported zero violations.
