import pytest
from app.analytics.policy import simulate
from app.analytics.extensions import regression, nlp, finance


def test_seed_reproducibility_service_constraint_and_cost_math():
    first = simulate([0, 0, 3, 0, 8] * 8, 100, draws=1000, bootstrap=20)
    assert first == simulate([0, 0, 3, 0, 8] * 8, 100, draws=1000, bootstrap=20)
    assert first["optimized"]["fill_rate"] >= first["baseline"]["fill_rate"] - 1e-12
    assert first["optimized"]["stockout_probability"] <= 0.05 + 1e-12
    for policy in ("baseline", "optimized"):
        values = first[policy]
        assert values["inventory_value"] == values["stock"] * 100
        assert values["expected_annual_cost"] == pytest.approx(values["annual_holding_cost"] + values["expected_stockout_cost"] + values["expedite_spend"])


def test_zero_demand_no_fabricated_savings():
    result = simulate([0] * 30, 100, draws=100, bootstrap=10)
    assert result["annual_savings"] == 0
    assert result["optimized"]["stock"] == 0
    assert result["optimized"]["fill_rate"] == 1


def test_compute_bounds():
    with pytest.raises(ValueError):
        simulate([1, 2], 10, draws=10001)


def test_regression_and_nlp_metrics_come_from_heldout_examples():
    delay = regression()
    assert delay["test_rows"] == 120
    assert delay["mae_days"] >= 0
    assert 0 <= delay["interval_coverage"] <= 1
    comments = nlp()
    assert 0 <= comments["macro_f1"] <= 1
    assert comments["zero_shot_comparison"]["status"] == "not measured"


def test_finance_zero_consumption_is_undefined_dio():
    result = finance([[0] * 12], [{"optimized": {"inventory_value": 100, "annual_holding_cost": 20}}])
    assert result["inventory_days"] is None
    assert result["monthly"][0]["budget_variance"] == 10
