import numpy as np


def regression(seed=42):
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.metrics import mean_absolute_error, r2_score
    rng = np.random.default_rng(seed)
    count = 600
    supplier = rng.integers(0, 3, count)
    category = rng.integers(0, 3, count)
    season = rng.integers(1, 13, count)
    size = rng.integers(1, 100, count)
    design = np.column_stack([supplier, category, season, size])
    actual = np.maximum(1, 15 + supplier * 4 + category * 2 + 0.15 * size + 5 * np.sin(season * np.pi / 6) + rng.normal(0, 3, count))
    fitted = RandomForestRegressor(n_estimators=60, max_depth=6, random_state=seed, n_jobs=1).fit(design[:360], actual[:360])
    residuals = actual[360:480] - fitted.predict(design[360:480])
    lower, upper = np.quantile(residuals, [0.05, 0.95])
    prediction = fitted.predict(design[480:])
    per_part = []
    for index in range(24):
        estimate = float(fitted.predict([[index % 3, index % 3, 6, 10 + index]])[0])
        per_part.append({"part_id": f"P{index + 1:04}", "predicted_delay_days": estimate,
                         "lower_days": max(0, estimate + float(lower)), "upper_days": estimate + float(upper)})
    return {"synthetic": True, "train_rows": 360, "calibration_rows": 120, "test_rows": 120,
            "mae_days": float(mean_absolute_error(actual[480:], prediction)), "r2": float(r2_score(actual[480:], prediction)),
            "interval_coverage": float(np.mean((actual[480:] >= prediction + lower) & (actual[480:] <= prediction + upper))),
            "feature_importance": dict(zip(["supplier", "category", "season", "order_size"], fitted.feature_importances_.tolist())),
            "parts": per_part}


def nlp(seed=42):
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import make_pipeline
    from sklearn.metrics import f1_score, classification_report
    templates = {
        "late_delivery": ["shipment arrived late", "delivery delayed by supplier", "part overdue for service", "missed promised delivery"],
        "wrong_part": ["incorrect component received", "wrong part in shipment", "mismatched item code delivered", "ordered part differs from received item"],
        "quality_defect": ["component failed quality inspection", "defective part malfunction", "quality test failed", "manufacturing defect found"],
        "damaged_in_transit": ["package damaged in transit", "shipping damage crushed part", "broken packaging on arrival", "transport damage visible"],
    }
    training, labels, testing, expected = [], [], [], []
    for label, phrases in templates.items():
        for index, phrase in enumerate(phrases):
            for sample in range(12):
                text = f"{phrase}; synthetic service order {sample} depot {sample % 3}"
                if index == 3:
                    testing.append(text)
                    expected.append(label)
                else:
                    training.append(text)
                    labels.append(label)
    model = make_pipeline(TfidfVectorizer(ngram_range=(1, 2)), LogisticRegression(max_iter=300, random_state=seed))
    model.fit(training, labels)
    predicted = model.predict(testing)
    return {"synthetic_comments_and_labels": True, "split": "held-out phrase template per category; small artificial task",
            "train_rows": len(training), "test_rows": len(testing), "macro_f1": float(f1_score(expected, predicted, average="macro")),
            "classification_report": classification_report(expected, predicted, output_dict=True, zero_division=0),
            "zero_shot_comparison": {"status": "not measured", "reason": "No external or local zero-shot model configured"},
            "risk_flags": [{"part_id": f"P{index + 1:04}", "supplier_id": f"SUP-{index % 3}", "category": str(predicted[index % len(predicted)])}
                           for index in range(24)]}


def distributions(values, seed=42):
    from scipy import stats
    values = np.asarray(values)
    mean, variance = float(values.mean()), float(values.var())
    candidates = []
    for name, distribution, params, parameter_count in [
        ("poisson", stats.poisson, (max(mean, 1e-9),), 1),
        ("negative_binomial", stats.nbinom,
         (max(mean * mean / max(variance - mean, 1e-6), 1e-6), min(max(mean / max(variance, mean + 1e-6), 1e-6), 0.999999)), 2)]:
        loglik = float(distribution.logpmf(values, *params).sum())
        statistic, probability = stats.kstest(values, distribution.cdf, args=params)
        candidates.append({"name": name, "aic": 2 * parameter_count - 2 * loglik,
                           "ks_statistic": float(statistic), "ks_pvalue": float(probability)})
    rng = np.random.default_rng(seed)
    lead_samples = rng.lognormal(0, 0.25, 200)
    leads = []
    for name, distribution in (("gamma", stats.gamma), ("lognormal", stats.lognorm)):
        params = distribution.fit(lead_samples, floc=0)
        statistic, probability = stats.kstest(lead_samples, distribution.cdf, args=params)
        leads.append({"name": name, "aic": 4 - 2 * float(distribution.logpdf(lead_samples, *params).sum()),
                      "ks_statistic": float(statistic), "ks_pvalue": float(probability)})
    return {"demand_candidates": candidates, "lead_candidates": leads,
            "limitations": "Lead observations synthetic. KS p-values are descriptive only: fitted parameters and discrete demand invalidate standard calibration."}


def finance(series, policies):
    months = []
    inventory = sum(item["optimized"]["inventory_value"] for item in policies)
    annual_consumption_cost = sum(np.mean(values[-12:]) * 12 * (20 + index * 13) for index, values in enumerate(series))
    for month in range(1, 13):
        budget = sum((10 + index) * (20 + index * 13) for index in range(len(series)))
        actual = sum((10 + index) * (20 + index * 13 + month % 3) for index in range(len(series)))
        months.append({"period": f"2002-{month:02}", "budget": budget, "actual": actual,
                       "budget_variance": actual - budget, "purchase_price_variance": actual - budget,
                       "expedite_spend": 25 * len(series) if month % 4 == 0 else 0})
    return {"currency": "USD", "synthetic": True, "inventory_days": inventory / annual_consumption_cost * 365 if annual_consumption_cost else None,
            "dio_basis": "Recommended stock value / trailing annual demand at synthetic standard cost * 365; not audited COGS.",
            "working_capital": inventory, "carrying_cost": sum(item["optimized"]["annual_holding_cost"] for item in policies),
            "monthly": months}
