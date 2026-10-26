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
                  "- Zero-shot classifier comparison: not measured"]
    elif path.stem == "benchmark":
        lines += [f'- Parts: {artifact["parts_count"]}', f'- Runtime seconds: {artifact["runtime_seconds"]}']
        for model, values in artifact["model_errors"].items():
            lines.append(f'- {model}: MAE {values["mae"]}, RMSE {values["rmse"]}')
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
