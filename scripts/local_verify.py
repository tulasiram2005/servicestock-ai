import json
import os
from pathlib import Path
import subprocess
import time
from urllib.request import Request, urlopen

root = Path(__file__).resolve().parents[1]
env = dict(line.split("=", 1) for line in (root / ".env").read_text().splitlines() if "=" in line)
def call(path, payload=None, token=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = "Bearer " + token
    request = Request("http://127.0.0.1:8000" + path, data=json.dumps(payload).encode() if payload else None, headers=headers)
    with urlopen(request, timeout=20) as response:
        return json.load(response)
token = call("/api/auth/login", {"username":"admin","password":env["ADMIN_PASSWORD"]})["access_token"]
job = call("/api/whatif", {"idempotency_key":"verify-" + str(time.time()), "service_level":0.95}, token)
for attempt in range(20):
    status = call("/api/jobs/" + job["job_id"], token=token)
    if status["status"] in {"succeeded", "dead"}:
        break
    time.sleep(0.2)
assert status["status"] == "succeeded", status["status"]
budget = call("/api/admin/usage", token=token)
artifact = {"measured_at":time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "environment":"local Docker Compose", "job_status":status["status"],
            "job_progress":status["progress"], "database_bytes":budget["database_bytes"],
            "row_counts":budget["row_counts"], "external_llm_calls":budget["llm_external_calls"]}
(root / "results/local_integration.json").write_text(json.dumps(artifact,indent=2))
request = Request("http://127.0.0.1:8000/api/reports/review.pdf",headers={"Authorization":"Bearer "+token})
with urlopen(request, timeout=20) as response:
    report = response.read()
target = root.parent.parent / "work/review.pdf"
target.parent.mkdir(exist_ok=True)
target.write_bytes(report)
print(json.dumps({key:artifact[key] for key in ("job_status","job_progress","database_bytes")}))
