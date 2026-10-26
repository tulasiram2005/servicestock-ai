# Free tier to scale

Current design is scale-ready, not scale-proven. To scale later (not enabled here):
1. Replace embedded Worker wake with a durable external wake transport and separately hosted worker.
2. Implement RateLimiter and cache interfaces with distributed storage, preserving budget guards.
3. Add read replicas through Store routing; preserve read-after-write behavior.
4. Move large compute to separately budgeted batch workers; keep artifact contracts stable.
5. Partition demand_history by period and retain composite keys.
6. Add distributed daily provider counters and key rotation before multiple API replicas.

All such infrastructure changes require a new deployment decision; none is provisioned by this repo.
