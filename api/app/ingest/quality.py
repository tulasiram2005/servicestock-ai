from datetime import datetime
import math


def validate(rows, part_ids, location_ids):
    accepted, issues, seen = [], [], set()
    for index, row in enumerate(rows):
        rule = None
        key = (row.get("part_id"), row.get("location_id"), row.get("period"))
        if any(row.get(name) is None for name in ("part_id", "location_id", "period", "qty")):
            rule = "completeness"
        elif row["part_id"] not in part_ids or row["location_id"] not in location_ids:
            rule = "referential_integrity"
        else:
            try:
                parsed = datetime.strptime(row["period"], "%Y-%m")
                if parsed.strftime("%Y-%m") != row["period"]:
                    raise ValueError()
                quantity = float(row["qty"])
                if isinstance(row["qty"], bool) or not math.isfinite(quantity) or quantity < 0:
                    raise ValueError()
            except (ValueError, TypeError, OverflowError):
                rule = "validity"
        if rule is None and key in seen:
            rule = "duplicate"
        if rule:
            safe = {str(key): str(value)[:240] for key, value in row.items()}
            issues.append({"row_index": index, "rule": rule, "row_data": safe, "quarantined": True})
        else:
            seen.add(key)
            accepted.append({**row, "qty": float(row["qty"])})
    by_part = {}
    for row in accepted:
        by_part.setdefault(row["part_id"], []).append(row["qty"])
    for part, values in by_part.items():
        mean = sum(values) / len(values)
        deviation = (sum((value - mean) ** 2 for value in values) / len(values)) ** 0.5
        for row in accepted:
            if row["part_id"] == part and deviation and row["qty"] > mean + 4 * deviation:
                issues.append({"row_index": None, "rule": "outlier", "row_data": row, "quarantined": False})
    return accepted, {"rows_received": len(rows), "rows_accepted": len(accepted),
                      "quarantined": len(rows) - len(accepted),
                      "quality_score": 100 * len(accepted) / len(rows) if rows else None, "issues": issues}
