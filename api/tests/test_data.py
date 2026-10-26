import pytest
from hypothesis import given, strategies as st
from sqlalchemy import select, func
from sqlalchemy.dialects import mssql
from sqlalchemy.schema import CreateTable

from app.db import schema as db
from app.db.store import Store
from app.ingest.seed import seed
from app.ingest.quality import validate


@pytest.fixture
def store():
    instance = Store("sqlite://")
    db.metadata.create_all(instance.engine)
    seed(instance)
    yield instance
    instance.engine.dispose()


def test_seed_quarantines_bad_rows_and_is_idempotent(store):
    with store.transaction() as connection:
        quality = connection.scalar(select(db.artifacts["dq_runs"].c.payload))
        assert quality["quarantined"] == 3
        assert {item["rule"] for item in quality["issues"]} >= {"duplicate", "validity", "referential_integrity"}
        assert connection.scalar(select(func.count()).select_from(db.parts)) == 24
    assert seed(store)["status"] == "already_seeded"


@given(st.floats(allow_nan=True, allow_infinity=True))
def test_negative_or_nonfinite_quantities_are_quarantined(quantity):
    import math
    accepted, report = validate([{"part_id": "P1", "location_id": "L1", "period": "2020-01", "qty": quantity}], {"P1"}, {"L1"})
    assert bool(accepted) == (math.isfinite(quantity) and quantity >= 0)


def test_dates_and_missing_values():
    rows = [{"part_id": "P1", "location_id": "L1", "period": "2020-13", "qty": 1}, {}]
    accepted, report = validate(rows, {"P1"}, {"L1"})
    assert not accepted
    assert report["quarantined"] == 2


def test_schema_compiles_for_sql_server():
    for table in db.metadata.sorted_tables:
        assert str(CreateTable(table).compile(dialect=mssql.dialect()))


def test_demand_foreign_keys_and_uniqueness(store):
    from sqlalchemy.exc import IntegrityError
    with pytest.raises(IntegrityError), store.transaction() as connection:
        connection.execute(db.demand_history.insert().values(part_id="NO", location_id="LOC-1", period="2020-01", qty=1))
