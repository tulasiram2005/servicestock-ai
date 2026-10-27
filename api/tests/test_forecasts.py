import numpy as np
import pytest

from app.analytics.forecast import abc, classify, predict, error_metrics, backtest
from app.analytics.forecast import calibrated_intervals, interval_backtest


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


def test_calibrated_constant_demand_and_heldout_coverage():
    bounds = calibrated_intervals([5]*40, 'naive', 12)
    assert bounds['lower'] == bounds['upper'] == bounds['service_upper'] == [5]*12
    assert bounds['calibration_counts'][0] == 24
    assert bounds['calibration_counts'][-1] == 13
    measured = interval_backtest([5]*40, 'naive')
    assert measured['evaluated_origins'] == 6
    assert measured['interval_coverage'] == measured['service_level_hit_rate'] == 1
    assert measured['mean_interval_width'] == 0


def test_interval_backtest_does_not_use_target_observation_for_calibration():
    measured = interval_backtest([5]*39+[1000], 'naive')
    assert measured['interval_coverage'] == pytest.approx(5/6)
    assert measured['service_level_hit_rate'] == pytest.approx(5/6)
    assert measured['mean_interval_width'] == 0


def test_insufficient_interval_history_is_explicitly_unmeasured():
    bounds = calibrated_intervals([5]*14, 'naive', 3)
    assert bounds['lower'] == [None]*3
    assert bounds['calibration_counts'] == [0]*3
    with pytest.raises(ValueError):
        calibrated_intervals([5]*40, 'naive', coverage=1)


def test_multistep_coverage_counts_and_unavailable_horizons():
    result=interval_backtest([5]*40,'naive',12)
    assert [h['evaluated_origins'] for h in result['by_horizon']]==[6,5,4,3,2,1,0,0,0,0,0,0]
    assert all(h['interval_coverage']==1 for h in result['by_horizon'][:6])
    assert all(h['interval_coverage'] is None for h in result['by_horizon'][6:])


def test_multistep_predictions_cannot_calibrate_against_future_targets():
    result=interval_backtest([5]*39+[1000],'naive',6)
    for row in result['by_horizon']:
        count=row['evaluated_origins']
        assert row['interval_coverage']==pytest.approx((count-1)/count)
        assert row['mean_interval_width']==0
    with pytest.raises(ValueError):
        interval_backtest([5]*40,'naive',0)
