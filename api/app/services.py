import json
import time
import uuid
from pathlib import Path

from fastapi import HTTPException
from sqlalchemy import select, func, delete, text

from .db import schema as db


def publish(store, directory):
    count = 0
    with store.transaction() as connection:
        for path in sorted(Path(directory).glob("*.json")):
            if path.stat().st_size > 5_000_000:
                raise ValueError("Artifact too large")
            payload = json.loads(path.read_text())
            connection.execute(delete(db.results).where(db.results.c.id == path.stem))
            connection.execute(db.results.insert().values(id=path.stem, payload=payload, created_at=time.time()))
            count += 1
    return count


def artifact(store, name):
    with store.transaction() as connection:
        payload = connection.scalar(select(db.results.c.payload).where(db.results.c.id == name))
    if payload is None:
        raise HTTPException(503, "Precomputed results are not available yet")
    return payload


def part_detail(store, part_id):
    with store.transaction() as connection:
        part = connection.execute(select(db.parts).where(db.parts.c.id == part_id)).mappings().first()
        if not part:
            raise HTTPException(404, "Part not found")
        history = connection.execute(select(db.demand_history.c.period, db.demand_history.c.qty).where(
            db.demand_history.c.part_id == part_id).order_by(db.demand_history.c.period).limit(120)).mappings().all()
    benchmark, analytics = artifact(store, "benchmark"), artifact(store, "analytics")
    forecast = next((item for item in benchmark["parts"] if item["part_id"] == part_id), None)
    policy = next((item for item in analytics["policies"] if item["part_id"] == part_id), None)
    return {"part": dict(part), "history": [dict(row) for row in history], "forecast": forecast,
            "policy": policy, "lead_sensitivity": sorted([
                {"lead_time_multiplier": cell["lead_time_multiplier"],
                 "annual_cost": cell["optimized"]["expected_annual_cost"],
                 "stock": cell["optimized"]["stock"], "fill_rate": cell["optimized"]["fill_rate"]}
                for cell in analytics["grid"] if policy and cell["part_id"] == part_id
                and cell["target_service_level"] == policy["target_service_level"]
                and cell["holding_rate"] == policy["holding_rate"]], key=lambda cell: cell["lead_time_multiplier"]),
            "synthetic_cost_assumptions": True, "source_id": "analytics:" + part_id}


def whatif(store, payload):
    analytics = artifact(store, "analytics")
    part_id = payload.get("part_id")
    cells = analytics["grid"]
    desired = (payload["service_level"], payload["holding_cost_rate"], payload["lead_time_multiplier"])
    nearest = min(cells, key=lambda cell: ((cell["target_service_level"] - desired[0]) / 0.099) ** 2 +
                  ((cell["holding_rate"] - desired[1]) / 0.99) ** 2 + ((cell["lead_time_multiplier"] - desired[2]) / 2.5) ** 2)
    selected = [cell for cell in cells if (cell["target_service_level"], cell["holding_rate"], cell["lead_time_multiplier"]) ==
                (nearest["target_service_level"], nearest["holding_rate"], nearest["lead_time_multiplier"])
                and (not part_id or cell["part_id"] == part_id)]
    if part_id and not selected:
        raise HTTPException(404, "Part not found")
    return {"mode": "precomputed_grid", "notice": "Snapped to the nearest precomputed grid cell; no live Monte Carlo computation.",
            "requested": payload, "used": {key: nearest[key] for key in ("target_service_level", "holding_rate", "lead_time_multiplier")},
            "parts": selected, "annual_savings": sum(cell["annual_savings"] for cell in selected),
            "working_capital_freed": sum(cell["working_capital_freed"] for cell in selected),
            "source_id": "analytics:grid", "synthetic_cost_assumptions": True}


def retain(store, days):
    cutoff, deleted = time.time() - days * 86400, {}
    with store.transaction() as connection:
        for table in [*db.artifacts.values(), db.audit_log, db.tool_call_log, db.data_quality_issues]:
            deleted[table.name] = connection.execute(delete(table).where(table.c.created_at < cutoff)).rowcount
        deleted['llm_daily_usage'] = connection.execute(delete(db.llm_daily_usage).where(
            db.llm_daily_usage.c.day < int(cutoff // 86400))).rowcount
        connection.execute(delete(db.refresh_tokens).where(db.refresh_tokens.c.expires_at < time.time()))
        connection.execute(delete(db.idempotency_keys).where(db.idempotency_keys.c.created_at < cutoff))
        deleted["jobs"] = connection.execute(delete(db.jobs).where(db.jobs.c.updated_at < cutoff,
            db.jobs.c.status.in_(["dead", "succeeded"]))).rowcount
    return {"deleted": deleted, "retention_days": days}


def usage(store, settings):
    with store.transaction() as connection:
        size = connection.scalar(text("SELECT pg_database_size(current_database())")) if store.engine.dialect.name == "postgresql" else None
        counts = {name: connection.scalar(select(func.count()).select_from(table)) for name, table in db.metadata.tables.items()}
    return {"database_bytes": size, "target_bytes": settings.db_target_bytes, "limit_bytes": settings.db_limit_bytes,
            "row_counts": counts, "above_target": size >= settings.db_target_bytes if size is not None else None,
            "llm_external_calls": 0, "llm_mode": "mock", "provider_compute_usage": "not measured; inspect provider dashboard"}


def handle_job(store, settings, kind, payload):
    if kind == "whatif":
        return whatif(store, payload)
    if kind == "retention":
        return retain(store, settings.retention_days)
    if kind == "report":
        return {"download_path": "/api/reports/review.pdf", "storage": "generated on demand, never persisted"}
    raise ValueError("Unsupported job kind")
