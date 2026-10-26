# Performance evidence

Forecast and simulation runtimes are in results/benchmark.json and results/analytics.json.
Local Locust smoke is recorded in results/load.json; it is a tiny single-user run, not a load-capacity measurement.
Lighthouse login scores and axe configuration-page results are in results/ui.json.
No production throughput or deployed cold-start/warm latency has been measured.
No scale claim is justified by the 24-series demo.

Local browser flow and axe results are recorded when tests complete. Database access uses
keyset pagination for part lists, composite demand keys and bounded tool results. Query plans
for the five slowest queries, N+1 profiling and k6/Locust workload measurements remain pending.
