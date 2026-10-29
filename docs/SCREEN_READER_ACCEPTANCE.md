# Human screen-reader acceptance

Status: USER-REPORTED CHECK, acceptance evidence pending. On 2026-10-29 the user reported trying the app and finding no obvious gap, but explicitly said they were unsure. This is exploratory feedback, not a formal acceptance pass. On 2026-10-28 the user said they checked, but did not supply platform/version, spoken output or per-task results. The rows below remain unverified. Automated axe and keyboard results do not satisfy this acceptance test.
Use the offline local demo with synthetic data; no external service or purchase is needed.
A person must listen to the output and report results. Do not record passwords or tokens.

Record tester, date, OS, browser version, screen reader/version and application commit.
For each step record pass/fail, actual spoken result and any reproduction details.

| Task | Expected result | Human result |
| --- | --- | --- |
| Open login; move through fields | Each field has a meaningful name; password is masked | Not run |
| Activate Skip to content | Focus moves past repeated navigation to main content | Not run |
| Submit invalid login | Error is discoverable and focus is usable for retry | Not run |
| Log in and navigate workspace | Navigation, selected view and headings are understandable | Not run |
| Filter Parts Explorer and open a part | Controls and results are named; changed results are discoverable | Not run |
| Inspect chart alternative tables | Headers, values, units and missing data are understandable | Not run |
| Submit an assistant question | Busy, completion, errors and cited tool results can be discovered | Not run |
| Submit Policy Lab job | Progress and terminal status can be read without losing navigation | Not run |
| Change configuration selection | Selected state and updated impact are understandable | Not run |
| Sign out and return to login | Focus returns to usable login content; no stale private data | Not run |

Test both themes and zoomed text. Report any focus trap, unnamed control, inaccessible
error or missing chart alternative as a blocking defect. A successful single-platform
pass does not establish compatibility with every browser or assistive technology.
