# Measured results

Generated from results/*.json. All costs and lead times are synthetic assumptions.

## analytics

Source: results/analytics.json

- inventory_value: 6226.0
- working_capital_freed: -2158.0
- annual_savings: 421.08382292140453
- mean_part_fill_rate: 0.977132729211127
- mean_part_stockout_probability: 0.002979166666666667
- Regression MAE days: 2.6652541721114136
- Regression R2: 0.8044132784279832
- Synthetic NLP macro-F1: 0.6666666666666666
- Zero-shot classifier comparison: not measured

## bandit

Source: results/bandit.json

- Reported medium/high findings: 0

## benchmark

Source: results/benchmark.json

- Parts: 24
- Runtime seconds: 1.9776042909943499
- naive: MAE 0.03472222222222222, RMSE 0.06512286786846311
- seasonal_naive: MAE 0.041666666666666664, RMSE 0.09209764296021157
- croston: MAE 0.2062493782015649, RMSE 0.22167877002468536
- sba: MAE 0.19663135373593107, RMSE 0.2122803637178656
- tsb: MAE 0.059039743206296375, RMSE 0.07326378366184029
- lightgbm: MAE 0.059771783881595264, RMSE 0.07900683755117686

## load

Source: results/load.json

```json
{
  "environment": "local Docker Compose",
  "tool": "Locust",
  "requests": 9,
  "failures": 0,
  "p50_ms": 24,
  "p95_ms": 66,
  "requests_per_second": 0.5183519913800464,
  "users": 0,
  "deployed": "not measured",
  "note": "Short low-load local smoke; not capacity proof"
}
```

## local_integration

Source: results/local_integration.json

```json
{
  "measured_at": "2026-10-26T11:22:22Z",
  "environment": "local Docker Compose",
  "job_status": "succeeded",
  "job_progress": 100,
  "database_bytes": 9706519,
  "row_counts": {
    "roles": 3,
    "users": 2,
    "suppliers": 3,
    "locations": 1,
    "parts": 24,
    "demand_history": 1224,
    "lead_time_params": 24,
    "cost_params": 24,
    "product_models": 1,
    "option_groups": 2,
    "options": 4,
    "compatibility_rules": 1,
    "product_configs": 2,
    "config_bom": 5,
    "purchase_orders": 288,
    "staging_extracts": 24,
    "data_quality_issues": 40,
    "jobs": 1,
    "refresh_tokens": 2,
    "assistant_sessions": 1,
    "tool_call_log": 1,
    "audit_log": 3,
    "idempotency_keys": 0,
    "forecast_runs": 0,
    "forecasts": 0,
    "policies": 0,
    "simulation_runs": 0,
    "recommendations": 0,
    "kpi_snapshots": 0,
    "dq_runs": 1,
    "results": 4,
    "login_attempts": 0
  },
  "external_llm_calls": 0
}
```

## pip-audit

Source: results/pip-audit.json

- Reported dependency vulnerabilities: 0

## ui

Source: results/ui.json

```json
{
  "measured_at": "2026-10-26T16:42:42.576Z",
  "page": "Configurations",
  "axe_violations": [],
  "lighthouse": {
    "page": "Login",
    "measured_at": "2026-10-26T16:26:49.053Z",
    "scores": {
      "performance": 0.97,
      "accessibility": 1,
      "best-practices": 0.74,
      "seo": 1
    },
    "environment": "local Docker Chrome"
  }
}
```

Deployed latency and production throughput: not measured.

Negative working capital freed indicates additional investment, not released cash.
