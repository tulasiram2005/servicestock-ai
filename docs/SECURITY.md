# Security policy

This application is a demonstration, not certified production software. Report vulnerabilities
privately to the repository maintainer; never include credentials or customer data in issues.

Implemented: Argon2id, 15-minute signed JWTs, database-checked roles/disabled users, hashed
refresh tokens with rotation/replay-family revocation, CSRF checks, exact CORS, bounded bodies,
login throttling/lockout, ORM queries, owner-scoped jobs/sessions, non-root API container,
in-memory request limits, structured request logs without body/header values.

Demo account is read-only. Credentials are generated into ignored local .env. Admin credentials
come from environment only. Public uploads are disabled; no upload endpoint exists.
Assistant output is text, not raw HTML. Only 11 typed tools exist and no SQL/shell tool exists.
PDF generation is planner/admin only.

Account initialization handles duplicate-identity races using transaction savepoints and
rechecks the identity before accepting a competing insert. Four independent Auth instances
against a shared SQLite file are tested; PostgreSQL/SQL Server concurrency validation remains.
Production permits plain HTTP only for GET /health and /health/live, returning static status
without database access so internal host probes work. Other routes still require HTTPS.

Limitations: rate limits are per process, not distributed. API audit writes are append-only
through normal application routes but the database role is not restricted by append-only
privileges. Retention is an explicit administrative exception. Signing-key rotation currently
invalidates all tokens; overlapping rotation is not implemented. External LLM adapters are
disabled/unimplemented. Optional development-only local Ollama routing is described in
LLM_PROVIDERS.md; model output cannot bypass tool validation or initiate report jobs.
Automated security scans and independent review remain required.


Login lockout decisions serialize per account in the database after password verification.
Five failures lock the account for five minutes; locked requests do not extend that period.
After expiry, a new wrong password starts a fresh count; successful login clears it.
Current password hash, role and disabled state are reread under the account lock, and
login audits commit with counter changes. Local PostgreSQL and shared SQLite concurrency
were tested on 2026-10-27; SQL Server runtime behavior is not yet verified.
