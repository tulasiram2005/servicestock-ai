import math
import numpy as np


def simulate(values, unit_cost, lead_mean=1.0, lead_std=0.25, target=0.95,
             holding_rate=0.2, lead_multiplier=1.0, draws=10000, seed=42, bootstrap=200):
    values = np.asarray(values, dtype=float)
    if not len(values) or np.any(values < 0) or not np.all(np.isfinite(values)):
        raise ValueError("Invalid demand")
    if not (0.8 <= target <= 0.999 and 0.01 <= holding_rate <= 1 and 0.5 <= lead_multiplier <= 3):
        raise ValueError("Invalid policy parameters")
    if not 100 <= draws <= 10000 or unit_cost <= 0 or lead_mean <= 0 or lead_std < 0:
        raise ValueError("Invalid compute scope or cost")
    rng = np.random.default_rng(seed)
    mean, std = lead_mean * lead_multiplier, lead_std * lead_multiplier
    sigma = math.sqrt(math.log1p((std / mean) ** 2))
    leads = rng.lognormal(math.log(mean) - sigma ** 2 / 2, sigma, draws)
    leads = np.clip(leads, 1 / 30, 12)
    whole = np.floor(leads).astype(int)
    samples = rng.choice(values, size=(draws, 13))
    lead_demand = (samples[:, :12] * (np.arange(12)[None, :] < whole[:, None])).sum(axis=1)
    lead_demand += samples[np.arange(draws), whole] * (leads - whole)
    lead_demand = np.ceil(lead_demand)
    total = float(lead_demand.sum())
    baseline_stock = int(math.ceil(np.mean(values) * 2))
    annual_factor = 12 / float(leads.mean())

    def evaluate(stock):
        shortage = np.maximum(lead_demand - stock, 0)
        remaining = np.maximum(stock - lead_demand, 0)
        holding = remaining * unit_cost * holding_rate
        penalty = shortage * unit_cost * 2 * annual_factor
        expedite = (shortage > 0) * 25 * annual_factor
        costs = holding + penalty + expedite
        return {"stock": int(stock), "fill_rate": 1 - float(shortage.sum()) / total if total else 1.0,
                "stockout_probability": float(np.mean(shortage > 0)), "inventory_value": float(stock * unit_cost),
                "annual_holding_cost": float(holding.mean()), "expected_stockout_cost": float(penalty.mean()),
                "expedite_spend": float(expedite.mean()), "expected_annual_cost": float(costs.mean())}, costs

    baseline, baseline_costs = evaluate(baseline_stock)
    lower = int(np.quantile(lead_demand, target, method="higher"))
    candidates = np.unique(np.r_[lower, baseline_stock, np.quantile(lead_demand, np.linspace(target, 1, 30), method="higher")]).astype(int)
    feasible = []
    for stock in candidates:
        metrics, costs = evaluate(stock)
        if metrics["fill_rate"] + 1e-12 >= max(target, baseline["fill_rate"]) and metrics["stockout_probability"] <= 1 - target + 1e-12:
            feasible.append((metrics, costs))
    optimized, optimized_costs = min(feasible, key=lambda pair: pair[0]["expected_annual_cost"])
    differences = baseline_costs - optimized_costs
    means = [float(rng.choice(differences, len(differences), replace=True).mean()) for repeat in range(bootstrap)]
    confidence = np.quantile(means, [0.025, 0.975]).tolist()
    centered = differences - differences.mean()
    null_means = [float(rng.choice(centered, len(centered), replace=True).mean()) for repeat in range(bootstrap)]
    p_value = (1 + sum(abs(value) >= abs(float(differences.mean())) for value in null_means)) / (bootstrap + 1)
    counts, bins = np.histogram(np.maximum(optimized["stock"] - lead_demand, 0) * unit_cost, bins=12)
    return {"baseline": baseline, "optimized": optimized, "annual_savings": float(differences.mean()),
            "working_capital_freed": baseline["inventory_value"] - optimized["inventory_value"],
            "savings_ci95": confidence, "paired_bootstrap_pvalue": p_value, "draws": draws, "seed": seed,
            "target_service_level": target, "holding_rate": holding_rate, "lead_time_multiplier": lead_multiplier,
            "histogram": {"counts": counts.tolist(), "bins_usd": bins.tolist()},
            "drivers": {"mean_monthly_demand": float(np.mean(values)), "demand_std": float(np.std(values)),
                        "mean_lead_months": mean, "lead_std_months": std, "unit_cost_usd": unit_cost},
            "method": "Empirical independent monthly demand, lognormal lead time, base-stock single lead-time cycle; annualized costs.",
            "synthetic_cost_assumptions": True}
