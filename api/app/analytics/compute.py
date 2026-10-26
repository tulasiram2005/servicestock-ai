import json
from pathlib import Path
import time
from datetime import datetime, timezone

from .policy import simulate
from .extensions import regression, nlp, distributions, finance

ROOT = Path(__file__).resolve().parents[3]


def run():
    started = time.perf_counter()
    benchmark = json.loads((ROOT / "results/benchmark.json").read_text())
    regression_result = regression()
    policies, grid = [], []
    for index, part in enumerate(benchmark["parts"]):
        delay = regression_result["parts"][index]["predicted_delay_days"] / 30
        result = simulate(part["history"], 20 + index * 13, lead_mean=1 + delay)
        policies.append({"part_id": part["part_id"], **result})
        for target in (0.9, 0.95, 0.99):
            for holding in (0.1, 0.2, 0.3):
                for multiplier in (0.5, 1.0, 2.0):
                    cell = simulate(part["history"], 20 + index * 13, lead_mean=1 + delay,
                                    target=target, holding_rate=holding, lead_multiplier=multiplier, bootstrap=20)
                    grid.append({"part_id": part["part_id"], **{key: cell[key] for key in
                        ("optimized", "baseline", "annual_savings", "working_capital_freed", "target_service_level", "holding_rate", "lead_time_multiplier")}})
    kpis = {"inventory_value": sum(item["optimized"]["inventory_value"] for item in policies),
            "working_capital_freed": sum(item["working_capital_freed"] for item in policies),
            "annual_savings": sum(item["annual_savings"] for item in policies),
            "mean_part_fill_rate": sum(item["optimized"]["fill_rate"] for item in policies) / len(policies),
            "mean_part_stockout_probability": sum(item["optimized"]["stockout_probability"] for item in policies) / len(policies)}
    artifact = {"generated_at": datetime.now(timezone.utc).isoformat(), "synthetic_cost_assumptions": True,
                "policies": policies, "grid": grid, "regression": regression_result, "nlp": nlp(),
                "distributions": distributions(benchmark["parts"][0]["history"]),
                "finance": finance([part["history"] for part in benchmark["parts"]], policies),
                "kpis": kpis, "runtime_seconds": time.perf_counter() - started}
    (ROOT / "results/analytics.json").write_text(json.dumps(artifact, indent=2, allow_nan=False))
    print(json.dumps({"kpis": kpis, "runtime_seconds": artifact["runtime_seconds"], "grid_cells": len(grid)}))


if __name__ == "__main__":
    run()
