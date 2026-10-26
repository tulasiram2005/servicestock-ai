from pathlib import Path
import pytest
import pyarrow.parquet as pq
from sqlalchemy import select, func

from app.db import schema as db
from app.db.store import Store
from app.ingest.seed import seed
from app.ingest.staging import generate_and_transform, transform
from app.services import publish
from app.export import export_all


@pytest.fixture
def store():
    instance = Store("sqlite://")
    db.metadata.create_all(instance.engine)
    seed(instance)
    publish(instance, Path(__file__).resolve().parents[2] / "results")
    return instance


def test_ten_extract_families_and_idempotent_etl(store):
    first = generate_and_transform(store)
    second = generate_and_transform(store)
    assert first == second
    assert first["tables"] == sorted(["MARA","MARC","MARD","MBEW","EKKO","EKPO","VBAK","VBAP","STKO","STPO"])
    assert first["inventory_rows"] == 24
    assert first["sales_rows"] == 288
    with store.transaction() as connection:
        assert connection.scalar(select(func.count()).select_from(db.warehouse_inventory)) == 24


def test_invalid_staging_input_is_not_silently_accepted():
    with pytest.raises(ValueError):
        transform([{"sap_table":"MARD","payload":{"MATNR":"MISSING","WERKS":"LOC-1","LABST":2}}], set())


def test_csv_parquet_exports_preserve_keys_and_kpis(store, tmp_path):
    generate_and_transform(store)
    counts = export_all(store, tmp_path)
    assert counts["kpi_scorecard"] == 1
    assert counts["warehouse_sales"] == 288
    assert pq.read_table(tmp_path / "parts.parquet").column("id")[0].as_py() == "P0001"
    assert (tmp_path / "manifest.json").exists()
