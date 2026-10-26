import csv
import io
import os
from pathlib import Path

from sqlalchemy import select
from .db import schema as db
from .db.store import Store

TABLES = {"parts": db.parts, "locations": db.locations, "suppliers": db.suppliers,
          "demand_history": db.demand_history, "purchase_orders": db.purchase_orders,
          "warehouse_inventory": db.warehouse_inventory, "warehouse_sales": db.warehouse_sales,
          "product_models": db.product_models, "config_bom": db.config_bom}


def table_rows(store, name):
    if name in {"kpi_scorecard", "monthly_finance"}:
        from .services import artifact
        analytics = artifact(store, "analytics")
        return [analytics["kpis"]] if name == "kpi_scorecard" else analytics["finance"]["monthly"]
    if name not in TABLES:
        raise ValueError("Unknown BI table")
    with store.transaction() as connection:
        rows = connection.execute(select(TABLES[name]).limit(100001)).mappings().all()
    if len(rows) > 100000:
        raise ValueError("Export exceeds row limit; no partial export produced")
    return [dict(row) for row in rows]


def csv_bytes(store, name):
    rows = table_rows(store, name)
    buffer = io.StringIO()
    fields = list(rows[0]) if rows else [column.name for column in TABLES[name].columns]
    writer = csv.DictWriter(buffer, fieldnames=fields)
    writer.writeheader()
    for row in rows:
        writer.writerow({key: "'" + value if isinstance(value, str) and value.startswith(("=", "+", "-", "@")) else value for key, value in row.items()})
    return buffer.getvalue().encode()


def export_all(store, target):
    import pyarrow as pa
    import pyarrow.parquet as pq
    import json
    target = Path(target)
    target.mkdir(parents=True, exist_ok=True)
    counts = {}
    for name in [*TABLES, "kpi_scorecard", "monthly_finance"]:
        content = csv_bytes(store, name)
        (target / (name + ".csv")).write_bytes(content)
        rows = table_rows(store, name)
        pq.write_table(pa.Table.from_pylist(rows), target / (name + ".parquet"))
        counts[name] = len(rows)
    (target / "manifest.json").write_text(json.dumps({"row_counts": counts,
        "label": "Public demand and synthetic business attributes; no SAP system was used."}, indent=2))
    return counts


if __name__ == "__main__":
    store = Store(os.environ["DATABASE_URL"])
    export_all(store, os.environ.get("BI_OUTPUT_DIR", "../results/bi"))
    print("Exported synthetic/public BI tables as CSV and Parquet.")
