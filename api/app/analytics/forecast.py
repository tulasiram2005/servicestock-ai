import numpy as np

MODELS = ("naive", "seasonal_naive", "croston", "sba", "tsb", "lightgbm")


def classify(values):
    values = np.asarray(values, dtype=float)
    positive = values[values > 0]
    if not len(positive):
        return {"adi": None, "cv2": None, "pattern": "intermittent", "no_demand": True}
    adi = len(values) / len(positive)
    cv2 = float(np.var(positive) / np.mean(positive) ** 2)
    pattern = ("lumpy" if cv2 >= 0.49 else "intermittent") if adi >= 1.32 else ("erratic" if cv2 >= 0.49 else "smooth")
    return {"adi": adi, "cv2": cv2, "pattern": pattern, "no_demand": False}


def abc(series, costs):
    annual = np.asarray([np.mean(values[-12:]) * 12 * cost for values, cost in zip(series, costs)])
    order = np.argsort(-annual)
    result, cumulative, total = {}, 0.0, float(annual.sum())
    for index in order:
        share_before = cumulative / total if total else 0
        result[int(index)] = "A" if share_before < 0.8 else ("B" if share_before < 0.95 else "C")
        cumulative += annual[index]
    return result


def features(values):
    values = np.asarray(values, dtype=float)
    return np.r_[values[-6:], np.mean(values[-6:]), np.std(values[-6:])]


def predict(values, model="sba", horizon=1, alpha=0.1):
    values = np.asarray(values, dtype=float)
    if model not in MODELS or not 1 <= horizon <= 12 or len(values) < 1:
        raise ValueError("Invalid forecast request")
    if not np.all(np.isfinite(values)) or np.any(values < 0):
        raise ValueError("Demand must be finite and nonnegative")
    if model == "seasonal_naive":
        return np.asarray([values[-12 + offset % 12] if len(values) >= 12 else values[-1] for offset in range(horizon)])
    if model == "naive":
        return np.repeat(values[-1], horizon)
    if model == "lightgbm":
        from lightgbm import LGBMRegressor
        if len(values) < 14:
            raise ValueError("LightGBM requires at least 14 periods")
        design = np.asarray([features(values[:end]) for end in range(6, len(values))])
        fitted = LGBMRegressor(n_estimators=30, max_depth=3, num_leaves=7, min_child_samples=3,
                              verbosity=-1, random_state=42, n_jobs=1).fit(design, values[6:])
        history, forecasts = list(values), []
        for step in range(horizon):
            estimate = max(0.0, float(fitted.booster_.predict(features(history).reshape(1, -1))[0]))
            forecasts.append(estimate)
            history.append(estimate)
        return np.asarray(forecasts)
    positive = np.flatnonzero(values > 0)
    if not len(positive):
        return np.zeros(horizon)
    first = int(positive[0])
    size, interval, elapsed = float(values[first]), float(first + 1), 1
    probability = 1 / interval
    for value in values[first + 1:]:
        if model == "tsb":
            probability += alpha * (float(value > 0) - probability)
        if value > 0:
            size += alpha * (value - size)
            interval += alpha * (elapsed - interval)
            elapsed = 1
        else:
            elapsed += 1
    estimate = size * probability if model == "tsb" else size / interval
    if model == "sba":
        estimate *= 1 - alpha / 2
    return np.repeat(estimate, horizon)


def intervals(values, predictions):
    radius = float(np.quantile(np.abs(np.diff(values)), 0.9)) if len(values) > 1 else 0
    return {"lower": np.maximum(0, predictions - radius).tolist(), "upper": (predictions + radius).tolist(),
            "method": "empirical historical absolute-change radius; coverage not guaranteed"}


def calibrated_intervals(values, model, horizon=12, coverage=0.9):
    """Rolling residual calibration using only observations available at issuance."""
    values = np.asarray(values, dtype=float)
    if not 0 < coverage < 1:
        raise ValueError("Coverage must be between zero and one")
    predictions = predict(values, model, horizon)
    residuals = [[] for _ in range(horizon)]
    for origin in range(max(14, len(values) - 24), len(values)):
        available = min(horizon, len(values) - origin)
        estimate = predict(values[:origin], model, available)
        for step in range(available):
            residuals[step].append(float(values[origin + step] - estimate[step]))
    lower, upper, service_upper, counts = [], [], [], []
    for point, errors in zip(predictions, residuals):
        counts.append(len(errors))
        if not errors:
            lower.append(None); upper.append(None); service_upper.append(None)
            continue
        lo, hi = np.quantile(errors, [(1-coverage)/2, 1-(1-coverage)/2], method="higher")
        lower.append(max(0.0, float(point + lo)))
        upper.append(max(lower[-1], float(point + hi)))
        service_upper.append(max(0.0, float(point + np.quantile(errors, 0.95, method="higher"))))
    return {"lower": lower, "upper": upper, "service_upper": service_upper,
            "nominal_coverage": coverage, "service_target": 0.95, "calibration_counts": counts,
            "method": "Per-horizon rolling forecast residual quantiles; maximum 24 past origins; empirical, no coverage guarantee"}


def interval_backtest(values, model):
    values = np.asarray(values, dtype=float)
    covered, service_hits, widths = [], [], []
    for origin in range(len(values)-6, len(values)):
        bounds = calibrated_intervals(values[:origin], model, 1)
        if bounds["lower"][0] is None:
            continue
        covered.append(bounds["lower"][0] <= values[origin] <= bounds["upper"][0])
        service_hits.append(values[origin] <= bounds["service_upper"][0])
        widths.append(bounds["upper"][0]-bounds["lower"][0])
    return {"evaluated_origins": len(covered), "interval_coverage": float(np.mean(covered)) if covered else None,
            "mean_interval_width": float(np.mean(widths)) if widths else None,
            "service_level_hit_rate": float(np.mean(service_hits)) if service_hits else None,
            "service_target": 0.95,
            "service_definition": "Fraction of one-month demand observations within the issued 95th-percentile upper bound; not inventory fill rate"}


def explain_ml(values):
    from lightgbm import LGBMRegressor
    design = np.asarray([features(values[:end]) for end in range(6, len(values))])
    fitted = LGBMRegressor(n_estimators=30, max_depth=3, num_leaves=7, min_child_samples=3,
                          verbosity=-1, random_state=42, n_jobs=1).fit(design, np.asarray(values[6:]))
    contributions = fitted.booster_.predict(features(values).reshape(1, -1), pred_contrib=True)[0]
    names = ["lag_6", "lag_5", "lag_4", "lag_3", "lag_2", "lag_1", "rolling_mean", "rolling_std", "base_value"]
    return {"method": "LightGBM TreeSHAP", "contributions": dict(zip(names, contributions.tolist()))}


def error_metrics(actual, predicted, training):
    actual, predicted = np.asarray(actual), np.asarray(predicted)
    errors = predicted - actual
    denominator = float(np.mean(np.abs(np.diff(training)))) if len(training) > 1 else 0
    return {"mae": float(np.mean(np.abs(errors))), "rmse": float(np.sqrt(np.mean(errors ** 2))),
            "mase": float(np.mean(np.abs(errors)) / denominator) if denominator else None,
            "bias": float(np.mean(errors))}


def backtest(values):
    values = np.asarray(values, dtype=float)
    if len(values) < 30:
        raise ValueError("Backtest requires 30 periods")
    results = {}
    for model in MODELS:
        validation = [predict(values[:origin], model)[0] for origin in range(len(values) - 12, len(values) - 6)]
        test = [predict(values[:origin], model)[0] for origin in range(len(values) - 6, len(values))]
        results[model] = {"validation_mae": float(np.mean(np.abs(values[-12:-6] - validation))),
                          **error_metrics(values[-6:], test, values[:-6]), "predictions": [float(value) for value in test]}
    winner = min(results, key=lambda model: results[model]["validation_mae"])
    return {"selected_model": winner, "models": results, "selection_periods": 6, "test_periods": 6,
            "selection_pattern": classify(values[:-12])["pattern"]}
