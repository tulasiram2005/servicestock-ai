import os
import json
from pathlib import Path
from locust import HttpUser, task, between, events


class Reader(HttpUser):
    wait_time = between(2, 3)
    def on_start(self):
        credentials = json.loads(Path(os.environ["LOAD_CREDENTIALS_FILE"]).read_text())
        response = self.client.post("/api/auth/login", json=credentials, name="/api/auth/login")
        self.token = response.json().get("access_token", "")
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
               "requests_per_second": total.total_rps, "users": environment.runner.user_count,
               "deployed": "not measured", "note": "Short low-load local smoke; not capacity proof"}
    Path("results/load.json").write_text(json.dumps(payload, indent=2))
