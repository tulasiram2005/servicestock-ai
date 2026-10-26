import os
from pathlib import Path
import time
import uuid

from sqlalchemy import select

from app.db import schema as db
from app.db.store import Store
from .loader import load
from .quality import validate


def seed(store, download=False):
    with store.transaction() as connection:
        if connection.scalar(select(db.parts.c.id).limit(1)):
            return {"status": "already_seeded"}
    series, provenance = load(cache=Path(__file__).resolve().parents[2] / "data/carparts.json", download=download)
    rows = []
    for index, values in enumerate(series):
        for month, qty in enumerate(values):
            rows.append({"part_id": f"P{index + 1:04}", "location_id": "LOC-1",
                         "period": f"{1998 + month // 12}-{month % 12 + 1:02}", "qty": qty})
    rows += [dict(rows[0]), {**rows[0], "qty": -1}, {**rows[0], "part_id": "UNKNOWN"}]
    accepted, quality = validate(rows, {f"P{index + 1:04}" for index in range(len(series))}, {"LOC-1"})
    run_id, now = uuid.uuid4().hex, time.time()
    with store.transaction() as connection:
        connection.execute(db.roles.insert(), [{"id": name, "name": name} for name in ("viewer", "planner", "admin")])
        connection.execute(db.suppliers.insert(), [{"id": f"SUP-{index}", "name": f"Synthetic supplier {index}"} for index in range(3)])
        connection.execute(db.locations.insert(), [{"id": "LOC-1", "name": "Synthetic service depot"}])
        for index in range(len(series)):
            part = f"P{index + 1:04}"
            cost = 20 + index * 13
            connection.execute(db.parts.insert().values(id=part, description=f"Synthetic service component {index + 1}",
                supplier_id=f"SUP-{index % 3}", category=["mechanical", "electrical", "consumable"][index % 3],
                unit_cost=cost, criticality=index % 3 + 1, synthetic=True))
            connection.execute(db.lead_time_params.insert().values(part_id=part, mean_months=1 + index % 3 * 0.25, std_months=0.25))
            connection.execute(db.cost_params.insert().values(part_id=part, holding_rate=0.2, stockout_penalty=cost * 2,
                                                               expedite_cost=25, synthetic=True))
            connection.execute(db.staging_extracts.insert().values(id=part, sap_table="MARA/MBEW", payload={"MATNR": part, "MAKTX": f"Synthetic service component {index + 1}", "STPRS": cost},
                                                                  label="SAP-style synthetic extract; no SAP system was used."))
            for month in range(1, 13):
                connection.execute(db.purchase_orders.insert().values(id=f"{part}-{month}", part_id=part,
                    period=f"2002-{month:02}", qty=10 + index, standard_price=cost, actual_price=cost + month % 3,
                    budget=(10 + index) * cost, expedite_spend=25 if month % 4 == 0 else 0))
        connection.execute(db.demand_history.insert(), accepted)
        for issue in quality["issues"]:
            connection.execute(db.data_quality_issues.insert().values(id=uuid.uuid4().hex, run_id=run_id, rule=issue["rule"],
                               row_data=issue["row_data"], quarantined=issue["quarantined"], created_at=now))
        connection.execute(db.artifacts["dq_runs"].insert().values(id=run_id, run_id=run_id, payload=quality, created_at=now))
        connection.execute(db.results.insert().values(id="provenance", payload=provenance, created_at=now))
        connection.execute(db.product_models.insert().values(id="MODEL-1", name="Synthetic service platform"))
        connection.execute(db.option_groups.insert().values(id="POWER", model_id="MODEL-1", minimum=1, maximum=1))
        connection.execute(db.option_groups.insert().values(id="EXTRA", model_id="MODEL-1", minimum=0, maximum=2))
        connection.execute(db.options.insert(), [{"id": "AC", "group_id": "POWER", "name": "AC power"},
            {"id": "DC", "group_id": "POWER", "name": "DC power"}, {"id": "SENSOR", "group_id": "EXTRA", "name": "Sensor"},
            {"id": "BATTERY", "group_id": "EXTRA", "name": "Battery"}])
        connection.execute(db.compatibility_rules.insert().values(id="R1", option_id="BATTERY", other_option_id="DC", kind="requires"))
        connection.execute(db.config_bom.insert(), [
            {"id": "B1", "model_id": "MODEL-1", "part_id": "P0001", "option_id": None, "qty": 2},
            {"id": "B2", "model_id": "MODEL-1", "part_id": "P0002", "option_id": "AC", "qty": 1},
            {"id": "B3", "model_id": "MODEL-1", "part_id": "P0003", "option_id": "DC", "qty": 1},
            {"id": "B4", "model_id": "MODEL-1", "part_id": "P0004", "option_id": "SENSOR", "qty": 1},
            {"id": "B5", "model_id": "MODEL-1", "part_id": "P0005", "option_id": "BATTERY", "qty": 1}])
        connection.execute(db.product_configs.insert(), [{"id": "CONFIG-AC", "model_id": "MODEL-1", "option_ids": ["AC"]},
            {"id": "CONFIG-DC", "model_id": "MODEL-1", "option_ids": ["DC", "BATTERY"]}])
    return {"status": "seeded", "quality": quality, "provenance": provenance}


if __name__ == "__main__":
    import json
    store = Store(os.environ["DATABASE_URL"])
    print(json.dumps(seed(store, download=os.getenv("DOWNLOAD_PUBLIC_DATA") == "true"), default=str))
    from app.services import publish
    from app.ingest.staging import generate_and_transform
    generate_and_transform(store)
    publish(store, os.getenv("RESULTS_DIR", str(Path(__file__).resolve().parents[3] / "results")))
