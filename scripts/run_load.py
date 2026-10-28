import argparse
import json
import os
from pathlib import Path
import subprocess
import tempfile

parser = argparse.ArgumentParser(description="Bounded local-only load smoke; no deployed capacity claim")
parser.add_argument('--users',type=int,choices=range(1,11),default=5)
parser.add_argument('--seconds',type=int,choices=range(10,61),default=30)
args=parser.parse_args()
root = Path(__file__).resolve().parents[1]
env = dict(line.split("=",1) for line in (root / ".env").read_text().splitlines() if "=" in line)
with tempfile.NamedTemporaryFile(mode="w", suffix=".json") as file:
    json.dump({"username":"demo","password":env["DEMO_PASSWORD"]},file)
    file.flush()
    subprocess.run([str(root / "api/.venv/bin/locust"), "-f", "scripts/locustfile.py", "--headless",
                    "--host", "http://127.0.0.1:8000", "-u", str(args.users), "-r", "1", "-t", str(args.seconds)+"s", "--only-summary"],
                   cwd=root, env={**os.environ,"LOAD_CREDENTIALS_FILE":file.name,"LOAD_TARGET_USERS":str(args.users),"LOAD_DURATION_SECONDS":str(args.seconds)}, check=True)
