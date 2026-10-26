import pytest
from fastapi import HTTPException

from app.configurations import evaluate, pooling, impact
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


def test_impact_reports_added_removed_and_unchanged_components(store):
    added = impact(store, "MODEL-1", ["AC"], ["AC", "SENSOR"])
    assert added["valid"]
    assert added["cost_change_usd"] == 59
    assert added["component_changes"] == [{"part_id": "P0004", "before_quantity": 0, "after_quantity": 1, "quantity_change": 1}]
    removed = impact(store, "MODEL-1", ["AC", "SENSOR"], ["AC"])
    assert removed["cost_change_usd"] == -59
    assert removed["component_changes"][0]["quantity_change"] == -1
    assert impact(store, "MODEL-1", ["AC"], ["AC"])["component_changes"] == []


def test_invalid_configuration_has_no_misleading_impact_values(store):
    result = impact(store, "MODEL-1", ["AC"], ["AC", "BATTERY"])
    assert not result["valid"]
    assert "cost_change_usd" not in result
