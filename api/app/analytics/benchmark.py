import json
from pathlib import Path
import time
from datetime import datetime, timezone

import numpy as np

from app.ingest.loader import load
from .forecast import abc, backtest, classify, predict, intervals, explain_ml

ROOT = Path(__file__).resolve().parents[4]


def run():
    started = time.perf_counter()
    series, provenance = load(cache=ROOT / "api/data/carparts.json")
    segments = abc(series, [20 + index * 13 for index in range(len(series))])
    parts = []
    for index, values in enumerate(series):
        evaluation = backtest(values)
        selected = evaluation["selected_model"]
        predictions = predict(values, selected, 12)
        parts.append({"part_id": f"P{index + 1:04}", "abc": segments[index], **classify(values),
                      "forecast": predictions.tolist(), "intervals": intervals(values, predictions),
                      "history": values, "ml_explanation": explain_ml(values), **evaluation})
    for pattern in {part["pattern"] for part in parts}:
        members = [part for part in parts if part["pattern"] == pattern]
        selected = min(members[0]["models"], key=lambda model: sum(part["models"][model]["validation_mae"] for part in members))
        for part in members:
            part["selected_model"] = selected
            predictions = predict(part["history"], selected, 12)
            part["forecast"] = predictions.tolist()
            part["intervals"] = intervals(part["history"], predictions)
    summary = {model: {"mae": float(np.mean([part["models"][model]["mae"] for part in parts])),
                       "rmse": float(np.mean([part["models"][model]["rmse"] for part in parts]))}
               for model in parts[0]["models"]}
    artifact = {"generated_at": datetime.now(timezone.utc).isoformat(), "dataset": provenance,
                "synthetic_cost_assumptions": True, "parts_count": len(parts), "parts": parts,
                "model_errors": summary, "runtime_seconds": time.perf_counter() - started,
                "selection": "Per-pattern aggregate validation MAE; final six rolling origins held out.",
                "segment_selection": "ADI/CV2 demand pattern"}
    target = ROOT / "results/benchmark.json"
    target.parent.mkdir(exist_ok=True)
    target.write_text(json.dumps(artifact, indent=2, allow_nan=False))
    return artifact


if __name__ == "__main__":
    artifact = run()
    print(json.dumps({key: artifact[key] for key in ("parts_count", "model_errors", "runtime_seconds")}))
