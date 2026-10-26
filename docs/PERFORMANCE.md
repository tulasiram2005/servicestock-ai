# Performance evidence

Forecast and simulation runtimes are in results/benchmark.json and results/analytics.json.
Local Locust smoke is recorded in results/load.json; it is a tiny single-user run, not a load-capacity measurement.
Lighthouse login scores and axe configuration-page results are in results/ui.json.
No production throughput or deployed cold-start/warm latency has been measured.
No scale claim is justified by the 24-series demo.

Local browser flow and axe results are recorded when tests complete. Database access uses
keyset pagination for part lists, composite demand keys and bounded tool results. Query plans
for the five slowest queries and broad N+1 profiling remain pending. The configuration BOM
now fetches component prices and lead times with one joined query instead of two queries per
component. A regression test verifies that increasing from two to 21 components does not
increase SELECT count. This is query-count evidence, not a measured production latency claim.
