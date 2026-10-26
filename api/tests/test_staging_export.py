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


@pytest.mark.parametrize("table,field", [("MARD", "LABST"), ("MBEW", "STPRS"), ("MARC", "PLIFZ"), ("VBAP", "KWMENG")])
@pytest.mark.parametrize("invalid", [float("nan"), float("inf"), -1])
def test_staging_rejects_nonfinite_and_negative_numbers(store, table, field, invalid):
    generate_and_transform(store)
    with store.transaction() as connection:
        extracts = [dict(row) for row in connection.execute(select(db.staging_extracts)).mappings()]
    next(row for row in extracts if row["sap_table"] == table)["payload"][field] = invalid
    with pytest.raises(ValueError, match="finite and nonnegative"):
        transform(extracts, {f"P{index:04}" for index in range(1, 25)})


def test_staging_rejects_duplicate_sales_and_invalid_months(store):
    generate_and_transform(store)
    with store.transaction() as connection:
        extracts = [dict(row) for row in connection.execute(select(db.staging_extracts)).mappings()]
    valid_parts = {f"P{index:04}" for index in range(1, 25)}
    duplicate = next(row for row in extracts if row["sap_table"] == "VBAP")
    with pytest.raises(ValueError, match="Duplicate"):
        transform([*extracts, duplicate], valid_parts)
    next(row for row in extracts if row["sap_table"] == "VBAK")["payload"]["AUDAT"] = "2002-13"
    with pytest.raises(ValueError):
        transform(extracts, valid_parts)


def test_csv_parquet_exports_preserve_keys_and_kpis(store, tmp_path):
    generate_and_transform(store)
    counts = export_all(store, tmp_path)
    assert counts["kpi_scorecard"] == 1
    assert counts["warehouse_sales"] == 288
    assert pq.read_table(tmp_path / "parts.parquet").column("id")[0].as_py() == "P0001"
    assert (tmp_path / "manifest.json").exists()
