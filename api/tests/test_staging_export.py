from pathlib import Path
import pytest
import pyarrow.parquet as pq
from sqlalchemy import select, func

from app.db import schema as db
from app.db.store import Store
from app.ingest.seed import seed
from app.ingest.staging import generate_and_transform, transform, transform_purchase_bom
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
    with store.transaction() as connection:
        before = {table.name: [dict(row) for row in connection.execute(select(table).order_by(table.c.id)).mappings()]
                  for table in (db.purchase_orders, db.config_bom)}
    first = generate_and_transform(store)
    second = generate_and_transform(store)
    assert first == second
    assert first["tables"] == sorted(["MARA","MARC","MARD","MBEW","EKKO","EKPO","VBAK","VBAP","STKO","STPO"])
    assert first["inventory_rows"] == 24
    assert first["sales_rows"] == 288
    assert first["purchase_rows"] == 288
    assert first["bom_rows"] == len(before['config_bom'])
    with store.transaction() as connection:
        assert connection.scalar(select(func.count()).select_from(db.warehouse_inventory)) == 24
        after = {table.name: [dict(row) for row in connection.execute(select(table).order_by(table.c.id)).mappings()]
                 for table in (db.purchase_orders, db.config_bom)}
    assert before == after


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


@pytest.mark.parametrize('family,field,value', [
    ('EKPO','NETPR','NaN'), ('EKPO','NETPR','1.001'), ('EKPO','MENGE',1.5),
    ('EKPO','MATNR','missing'), ('EKKO','WAERS','EUR'), ('EKKO','BEDAT','2002-99'),
    ('STPO','MENGE',0), ('STPO','MENGE',float('inf')), ('STKO','MODEL','missing'),
    ('STKO','OPTION','missing'), ('STPO','STLNR','missing')])
def test_purchase_bom_rejects_invalid_extracts(store, family, field, value):
    generate_and_transform(store)
    with store.transaction() as connection:
        extracts = [dict(row) for row in connection.execute(select(db.staging_extracts)).mappings()]
        parts = set(connection.scalars(select(db.parts.c.id)))
        models = set(connection.scalars(select(db.product_models.c.id)))
        option_models = dict(connection.execute(select(db.options.c.id, db.option_groups.c.model_id).join(
            db.option_groups, db.options.c.group_id == db.option_groups.c.id)).all())
    next(row for row in extracts if row['sap_table'] == family)['payload'][field] = value
    with pytest.raises(ValueError):
        transform_purchase_bom(extracts, parts, models, option_models)


def test_multiline_purchase_and_bom_preserve_every_detail():
    extracts = [
        {'sap_table':'EKKO','payload':{'EBELN':'PO1','BEDAT':'2026-01','WAERS':'USD'}},
        {'sap_table':'STKO','payload':{'STLNR':'BOM1','MODEL':'M1','OPTION':None}},
    ]
    for line, part in [('00010','P1'),('00020','P2')]:
        extracts += [
            {'sap_table':'EKPO','payload':{'EBELN':'PO1','EBELP':line,'MATNR':part,'MENGE':2,
             'NETPR':'3.00','Z_STANDARD_PRICE':'4.00','Z_BUDGET':'9.00','Z_EXPEDITE_SPEND':'1.00'}},
            {'sap_table':'STPO','payload':{'STLNR':'BOM1','POSNR':line,'IDNRK':part,'MENGE':2}},
        ]
    purchases, components = transform_purchase_bom(extracts, {'P1','P2'}, {'M1'}, {})
    assert [row['id'] for row in purchases] == ['PO1','PO1:20']
    assert [row['id'] for row in components] == ['BOM1','BOM1:20']
    assert sum(row['qty'] * row['actual_price'] for row in purchases) == 12
    assert sum(row['qty'] for row in components) == 4
    reversed_result = transform_purchase_bom(list(reversed(extracts)), {'P1','P2'}, {'M1'}, {})
    assert sorted(reversed_result[0], key=lambda r:r['id']) == purchases
    duplicate = {'sap_table':'EKPO','payload':dict(extracts[2]['payload'],EBELP='10')}
    with pytest.raises(ValueError, match='Duplicate staging detail'):
        transform_purchase_bom(extracts+[duplicate], {'P1','P2'}, {'M1'}, {})
    duplicate_bom = {'sap_table':'STPO','payload':dict(extracts[3]['payload'],POSNR='10')}
    with pytest.raises(ValueError, match='Duplicate staging detail'):
        transform_purchase_bom(extracts+[duplicate_bom], {'P1','P2'}, {'M1'}, {})
