import json
import os
from pathlib import Path
import subprocess
import tempfile

root = Path(__file__).resolve().parents[1]
env = dict(line.split("=",1) for line in (root / ".env").read_text().splitlines() if "=" in line)
with tempfile.NamedTemporaryFile(mode="w", suffix=".json") as file:
    json.dump({"username":"demo","password":env["DEMO_PASSWORD"]},file)
    file.flush()
    subprocess.run([str(root / "api/.venv/bin/locust"), "-f", "scripts/locustfile.py", "--headless",
                    "--host", "http://127.0.0.1:8000", "-u", "1", "-r", "1", "-t", "20s", "--only-summary"],
                   cwd=root, env={**os.environ,"LOAD_CREDENTIALS_FILE":file.name}, check=True)
