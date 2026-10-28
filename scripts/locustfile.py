import os
import json
from pathlib import Path
from locust import HttpUser, task, between, events
from locust.exception import StopUser
from collections import Counter
from datetime import datetime, timezone

status_counts = Counter()

@events.request.add_listener
def record_status(response=None, **kwargs):
    status_counts[str(response.status_code) if response is not None else "transport_error"] += 1


class Reader(HttpUser):
    wait_time = between(2, 3)
    def on_start(self):
        credentials = json.loads(Path(os.environ["LOAD_CREDENTIALS_FILE"]).read_text())
        response = self.client.post("/api/auth/login", json=credentials, name="/api/auth/login")
        if response.status_code != 200:
            raise StopUser()
        self.token = response.json().get("access_token", "")
        if not self.token:
            raise StopUser()
    @task
    def read_parts(self):
        self.client.get("/api/parts?limit=20", headers={"Authorization": "Bearer " + self.token}, name="/api/parts")
    @task
    def read_kpis(self):
        self.client.get("/api/kpis", headers={"Authorization": "Bearer " + self.token}, name="/api/kpis")


@events.quitting.add_listener
def results(environment, **kwargs):
    total = environment.stats.total
    payload = {"environment": "local Docker Compose", "tool": "Locust", "requests": total.num_requests,
               "failures": total.num_failures, "p50_ms": total.get_response_time_percentile(0.5),
               "p95_ms": total.get_response_time_percentile(0.95),
               "requests_per_second": total.total_rps, "target_users": int(os.environ.get("LOAD_TARGET_USERS", "1")),
               "duration_seconds": int(os.environ.get("LOAD_DURATION_SECONDS", "20")),
               "measured_at": datetime.now(timezone.utc).isoformat(),
               "http_status_counts": dict(status_counts),
               "endpoints": [{"method": entry.method, "name": entry.name, "requests": entry.num_requests,
                   "failures": entry.num_failures, "p95_ms": entry.get_response_time_percentile(0.95)}
                   for entry in environment.stats.entries.values()],
               "deployed": "not measured", "note": "Bounded local read workload using a shared demo account and unchanged rate limits; not production capacity proof"}
    temporary = Path("results/load.json.tmp")
    temporary.write_text(json.dumps(payload, indent=2)+"\n")
    temporary.replace("results/load.json")
