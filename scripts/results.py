import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
lines = ["# Measured results", "", "Generated from results/*.json. All costs and lead times are synthetic assumptions.", ""]
for path in sorted((root / "results").glob("*.json")):
    artifact = json.loads(path.read_text())
    lines += ["## " + path.stem, "", "Source: results/" + path.name, ""]
    if path.stem == "analytics":
        for name, value in artifact["kpis"].items():
            lines.append(f"- {name}: {value}")
        lines += [f'- Regression MAE days: {artifact["regression"]["mae_days"]}',
                  f'- Regression R2: {artifact["regression"]["r2"]}',
                  f'- Synthetic NLP macro-F1: {artifact["nlp"]["macro_f1"]}',
                  "- Zero-shot classifier comparison: see nlp_comparison below if present; otherwise not measured"]
    elif path.stem == "benchmark":
        lines += [f'- Parts: {artifact["parts_count"]}', f'- Runtime seconds: {artifact["runtime_seconds"]}']
        for model, values in artifact["model_errors"].items():
            lines.append(f'- {model}: MAE {values["mae"]}, RMSE {values["rmse"]}')
        horizons = {}
        for part in artifact["parts"]:
            for row in part.get("interval_backtest", {}).get("by_horizon", []):
                horizons.setdefault(row["horizon_months"], []).append(row)
        if horizons:
            lines += ["", "| Horizon (months) | Evaluated observations | Coverage | Mean width (units) |",
                      "|---|---|---|---|"]
            for horizon, rows in sorted(horizons.items()):
                n = sum(row["evaluated_origins"] for row in rows)
                covered = sum((row["interval_coverage"] or 0)*row["evaluated_origins"] for row in rows)
                width = sum((row["mean_interval_width"] or 0)*row["evaluated_origins"] for row in rows)
                coverage_label = f"{covered/n:.4f}" if n else "Not measured"
                width_label = f"{width/n:.4f}" if n else "Not measured"
                lines.append(f"| {horizon} | {n} | {coverage_label} | {width_label} |")
            lines += ["", "Final six held-out periods only; horizons have decreasing, overlapping samples.",
                      "Coverage is empirical, not guaranteed; target-month bounds are not cumulative lead-time demand."]
    elif path.stem == "nlp_comparison":
        lines += [f'- Model: {artifact["model"]}',
                  f'- Measured at: {artifact["measured_at"]}',
                  f'- Offline baseline macro-F1: {artifact["baseline_macro_f1"]:.4f}',
                  f'- Zero-shot macro-F1: {artifact["zero_shot_macro_f1"]:.4f}',
                  f'- Test rows: {artifact["test_rows"]}; unique held-out templates: {artifact["unique_heldout_templates"]}',
                  f'- Requests: {artifact["requests_attempted"]}; elapsed seconds: {artifact["elapsed_seconds"]}']
        lines += ['- Limitation: ' + value for value in artifact['limitations']]
    elif path.stem == "pip-audit":
        vulnerabilities = sum(len(item.get("vulns", [])) for item in artifact.get("dependencies", []))
        lines += [f"- Reported dependency vulnerabilities: {vulnerabilities}"]
    elif path.stem == "bandit":
        lines += [f'- Reported medium/high findings: {len(artifact.get("results", []))}']
    else:
        lines += ["```json", json.dumps(artifact, indent=2), "```"]
    lines.append("")
lines += ["Deployed latency and production throughput: not measured.", "",
          "Negative working capital freed indicates additional investment, not released cash."]
(root / "docs/RESULTS.md").write_text("\n".join(lines) + "\n")
print("Regenerated docs/RESULTS.md from run artifacts.")
