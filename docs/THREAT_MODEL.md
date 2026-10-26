# Threat model

| STRIDE threat | Control | Evidence / remaining risk |
|---|---|---|
| Spoofing | Argon2id, signed/expiring JWT, refresh rotation | test_security.py |
| Tampering | typed inputs, parameterized ORM, deny extra fields | test_api.py, test_assistant.py |
| Repudiation | login/tool/export audit rows | database permissions do not yet enforce append-only |
| Information disclosure | job/session owner checks, redacted logs | test_business_api.py, test_assistant.py |
| Denial of service | request, result, iteration and rate caps | tool wall-clock cancellation pending |
| Elevation | role checked against DB, planner/admin exports | test_security.py |

LLM controls: injection remains untrusted data; deterministic routing never executes data
instructions; results render as text; no external calls or spend occur. No model gets direct
database, file, or shell access. Provider-chain isolation must be reviewed before enabling it.

Browser, API, database, compute artifacts and optional future providers are separate trust
boundaries. Public data and synthetic assumptions are the only permitted external-model inputs.
