import hashlib
import io
import json
from pathlib import Path
import random
import urllib.request
import zipfile

PUBLIC_URL = "https://zenodo.org/records/4656021/files/car_parts_dataset_without_missing_values.zip?download=1"


def synthetic(count=24, periods=51, seed=42):
    rng = random.Random(seed)
    return [[float(rng.randint(1, 12)) if rng.random() < 0.12 + (part % 5) * 0.1 else 0.0
             for period in range(periods)] for part in range(count)]


def load(count=24, cache=None, download=False):
    cache = Path(cache) if cache else None
    if cache and cache.exists():
        payload = json.loads(cache.read_text())
        return payload["series"][:count], payload["provenance"]
    if download:
        try:
            with urllib.request.urlopen(PUBLIC_URL, timeout=20) as response:
                raw = response.read(1_000_001)
            if len(raw) > 1_000_000:
                raise ValueError("Download exceeds cap")
            with zipfile.ZipFile(io.BytesIO(raw)) as archive:
                member = next(item for item in archive.infolist() if item.filename.endswith(".tsf"))
                if member.file_size > 5_000_000:
                    raise ValueError("Expanded dataset exceeds cap")
                content = archive.read(member).decode("utf-8", errors="strict")
            lines = content.split("@data", 1)[1].strip().splitlines()
            series = [[float(value) for value in line.rsplit(":", 1)[-1].split(",")]
                      for line in lines if line.strip() and not line.startswith("#")]
            provenance = {"kind": "public", "url": PUBLIC_URL, "sha256": hashlib.sha256(raw).hexdigest(),
                          "note": "Monash car parts, source replaces missing observations with zeros; first series subset."}
            if cache:
                cache.parent.mkdir(parents=True, exist_ok=True)
                cache.write_text(json.dumps({"series": series, "provenance": provenance}))
            return series[:count], provenance
        except (OSError, ValueError, StopIteration, zipfile.BadZipFile):
            pass
    return synthetic(count), {"kind": "synthetic", "seed": 42,
                              "note": "Seeded intermittent generator; public dataset unavailable or offline mode."}
