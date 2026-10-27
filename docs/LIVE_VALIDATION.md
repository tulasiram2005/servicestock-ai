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

Run [40533154602](https://github.com/tulasiram2005/servicestock-ai/actions/runs/40533154602)
validated database creation, all migrations, quota concurrency and refresh-token concurrency.
The job-claim test failed; full compatibility remains unvalidated. The test now retries
transient empty claims with a ten-second deadline while retaining exact-once and complete
coverage assertions. A new run on the updated commit is required.

The manual-only workflow uses an x86-64 Ubuntu runner, SQL Server Developer, ephemeral
masked credentials, a 20-minute timeout and cleanup. Private Actions allowance and an
existing $0 budget were observed on 2026-10-27; the budget was not changed. No paid
infrastructure was provisioned. This ARM Mac is not used to claim SQL Server runtime support.

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
