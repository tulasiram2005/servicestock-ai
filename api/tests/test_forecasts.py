import numpy as np
import pytest

from app.analytics.forecast import abc, classify, predict, error_metrics, backtest


def test_croston_constant_and_zero():
    assert np.allclose(predict([5] * 30, "croston", 3), 5)
    for model in ("croston", "sba", "tsb"):
        assert np.all(predict([0] * 30, model) == 0)
    assert np.allclose(predict([5] * 30, "sba"), 4.75)


def test_patterns_and_abc():
    assert classify([1] * 30)["pattern"] == "smooth"
    assert classify([0, 0, 1] * 10)["pattern"] == "intermittent"
    assert classify([1, 1, 1, 20] * 10)["pattern"] == "erratic"
    assert classify([0, 0, 1, 0, 0, 20] * 10)["pattern"] == "lumpy"
    assert abc([[10], [1], [1]], [100, 1, 1])[0] == "A"


def test_zero_denominator_mase_is_undefined():
    assert error_metrics([0, 0], [0, 0], [0, 0])["mase"] is None


def test_backtest_is_reproducible_and_has_held_out_origins():
    values = [0, 0, 2, 0, 4] * 8
    first = backtest(values)
    assert first == backtest(values)
    assert len(first["models"]) == 6
    assert all(len(item["predictions"]) == 6 for item in first["models"].values())


def test_negative_input_rejected():
    with pytest.raises(ValueError):
        predict([-1, 2])


def test_future_test_demand_cannot_change_selection_pattern_or_validation():
    original = [2] * 40
    changed = original[:-6] + [0, 0, 0, 0, 0, 1000]
    before, after = backtest(original), backtest(changed)
    assert classify(original)["pattern"] != classify(changed)["pattern"]
    assert before["selection_pattern"] == after["selection_pattern"] == "smooth"
    assert before["selected_model"] == after["selected_model"]
    assert {key: value["validation_mae"] for key, value in before["models"].items()} == {
        key: value["validation_mae"] for key, value in after["models"].items()}
