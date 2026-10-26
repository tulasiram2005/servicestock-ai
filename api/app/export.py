import csv
import io
import os
from pathlib import Path

from sqlalchemy import select
from .db import schema as db
from .db.store import Store

TABLES = {"parts": db.parts, "locations": db.locations, "suppliers": db.suppliers,
          "demand_history": db.demand_history, "purchase_orders": db.purchase_orders}


def csv_bytes(store, name):
    if name not in TABLES:
        raise ValueError("Unknown BI table")
    with store.transaction() as connection:
        rows = connection.execute(select(TABLES[name]).limit(100000)).mappings().all()
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=[column.name for column in TABLES[name].columns])
    writer.writeheader()
    for row in rows:
        writer.writerow({key: "'" + value if isinstance(value, str) and value.startswith(("=", "+", "-", "@")) else value for key, value in row.items()})
    return buffer.getvalue().encode()


if __name__ == "__main__":
    import pyarrow as pa
    import pyarrow.parquet as pq
    import pandas as pd
    store = Store(os.environ["DATABASE_URL"])
    target = Path(os.environ.get("BI_OUTPUT_DIR", "../results/bi"))
    target.mkdir(parents=True, exist_ok=True)
    for name in TABLES:
        content = csv_bytes(store, name)
        (target / (name + ".csv")).write_bytes(content)
        pq.write_table(pa.Table.from_pandas(pd.read_csv(io.BytesIO(content))), target / (name + ".parquet"))
    print("Exported synthetic/public BI tables as CSV and Parquet.")
