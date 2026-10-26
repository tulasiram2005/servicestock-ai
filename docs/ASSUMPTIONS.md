# Assumptions and precedence

The single source of truth is ServiceStock_AI_Master_Prompt.md supplied on 2026-10-26.
Precedence: Part 3 free-tier overrides > Part 2 JD patch > Part 1.
P9 configuration is core, not optional. Azure/Celery/Redis/blob defaults are replaced.

- This is a personal synthetic demonstration, not a validated production inventory system.
- Currency is USD; periods are months; costs, lead times, criticality, suppliers, configurations,
  orders, invoices and comments are synthetic. No SAP system was used.
- Use deterministic seeded demand when a public dataset cannot be downloaded; label provenance.
- Implement phase acceptance in order; security work already in progress is retained.
- No cloud account billing changes, no paid services, no uptime pingers.
- Local setup writes generated secrets to ignored .env; production secrets are supplied manually.
- SQL Server runtime validation requires a compatible Linux container host; compilation alone
  is not evidence of working SQL Server integration.
