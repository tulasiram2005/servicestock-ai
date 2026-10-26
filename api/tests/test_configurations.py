import pytest
from fastapi import HTTPException

from app.configurations import evaluate, pooling
from app.db.store import Store
from app.db import schema as db
from app.ingest.seed import seed


@pytest.fixture
def store():
    instance = Store("sqlite://")
    db.metadata.create_all(instance.engine)
    seed(instance)
    return instance


def test_valid_bom_cost_and_parallel_lead(store):
    result = evaluate(store, "MODEL-1", ["AC"])
    assert result["valid"]
    assert result["cost_usd"] == 2 * 20 + 33
    assert result["lead_months"] == 1.25


def test_incompatible_missing_duplicate_and_unknown_options(store):
    assert not evaluate(store, "MODEL-1", ["AC", "BATTERY"])["valid"]
    assert not evaluate(store, "MODEL-1", [])["valid"]
    for options in (["AC", "AC"], ["UNKNOWN"]):
        with pytest.raises(HTTPException):
            evaluate(store, "MODEL-1", options)


def test_option_impact_and_commonality(store):
    base = evaluate(store, "MODEL-1", ["AC"])
    enhanced = evaluate(store, "MODEL-1", ["AC", "SENSOR"])
    assert enhanced["cost_usd"] - base["cost_usd"] == 59
    shared = next(part for part in pooling(store)["parts"] if part["part_id"] == "P0001")
    assert shared["commonality"] == 1
    assert shared["safety_stock_reduction_fraction"] == pytest.approx(1 - 1 / 2 ** 0.5)
