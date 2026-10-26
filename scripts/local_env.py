from pathlib import Path
import secrets

target = Path(__file__).resolve().parents[1] / ".env"
if not target.exists():
    values = {
        "JWT_SECRET": secrets.token_urlsafe(48),
        "DEMO_PASSWORD": secrets.token_urlsafe(18),
        "ADMIN_PASSWORD": secrets.token_urlsafe(24),
        "POSTGRES_PASSWORD": secrets.token_hex(24),
    }
    with open(target, "x", opener=lambda path, flags: __import__("os").open(path, flags, 0o600)) as output:
        output.write("\n".join(f"{key}={value}" for key, value in values.items()) + "\n")
print("Local credentials are stored in .env (not printed or committed).")
