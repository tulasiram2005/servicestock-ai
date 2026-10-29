# Provider follow-up — 2026-10-29

Added an opt-in Groq remote adapter with free-plan confirmation, public-prompt
restriction, fixed HTTPS endpoint, validated native/JSON tool plans, shared
quota controls, rate-limit backoff and offline fallback. Defaults stay offline.
No Groq account or credential is configured; live Groq validation is pending.

Verification: complete backend suite 250 passed, 4 skipped (18.43 seconds).
Hosted smoke 12/12 expected results at 09:59 UTC, including viewer denial of
admin access, refresh and logout. This is HTTP verification, not full browser
regression or evidence that this newly added adapter is deployed.

Render previously confirmed live backend 6dbc528 including durable token
reservations and native capability detection. The new Groq code requires a
subsequent deployment; account configuration remains off regardless.

Local Mistral warm-up succeeded, but native routing still fell back at 5.026s.
A successful native application call is not established. Formal human
screen-reader acceptance remains unverified; automated scans are not a substitute.
