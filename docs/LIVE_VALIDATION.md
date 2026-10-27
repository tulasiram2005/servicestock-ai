# Live validation status · 2026-10-27

## Gemini

Live smoke passed on 2026-10-27 at 16:08 IST using `gemini-3.5-flash-lite`.
One app-authored public KPI routing prompt returned the expected `get_kpis` selection
in 1.603 seconds. Evidence: `results/gemini_live_smoke.json`. This validates one routing
request, not model quality, all tools, or production readiness. The key is privately saved
in ignored `.env.gemini`; it is absent from reports and commits. Billing-disabled status
is based on user confirmation and the supplied Free tier screenshot, not a billing API.
Application defaults remain Mock and zero quotas. No paid service was enabled.

## SQL Server

Schema/statement compilation passes offline; runtime has not been validated. This Mac
is ARM64. Microsoft supports its SQL Server Linux container on Intel/AMD x86-64 Linux;
Rosetta/QEMU translation is not tested or supported. Verified 2026-10-27 against
[Microsoft container guidance](https://learn.microsoft.com/en-us/sql/linux/containers/deploy?view=sql-server-linux-ver15).
No unsupported container run is being presented as compatibility certification.

The existing `.github/workflows/sqlserver.yml` uses an x86 Linux runner and Developer
edition for testing. It remains gated to a public repository with the explicit
`SQLSERVER_TESTS_ENABLED=true` variable and `SQLSERVER_TEST_PASSWORD` secret. It applies
migrations and runs job-claim, quota-concurrency and refresh-token concurrency integration tests. The private GitHub repository now exists, but the public-only gate deliberately skips
this workflow; it has not run. No paid VM or database was provisioned.
A successful workflow is required before claiming SQL Server runtime compatibility.

## Local model

Installed Mistral was attempted twice; both attempts timed out under the app's five-second
request timeout and fell back. See results/live_model_smoke.json. This proves fallback
behavior for those attempts, not successful inference or quality.

## Private GitHub Actions eligibility · checked 2026-10-27

Keep the repository private. The current public-only workflow guard is a conservative
project choice, not a GitHub requirement. GitHub documents included private-repository
minutes/storage, and says usage is blocked after quota exhaustion if no valid payment
method is on file. See [official Actions billing documentation](https://docs.github.com/en/billing/concepts/product-billing/github-actions).
Before enabling one bounded private test, verify the account's remaining allowance and
no-charge configuration; do not add a card, enable paid usage, or change visibility.
Account verification could not proceed because local browser use is disabled in Work
settings. No SQL Server workflow was enabled or dispatched. Gemini single-request validation is
now complete as documented above; SQL Server runtime validation remains pending.
