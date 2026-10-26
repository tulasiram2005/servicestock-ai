from collections import defaultdict
import math

from fastapi import HTTPException
from sqlalchemy import select

from .db import schema as db


def catalog(store):
    with store.transaction() as connection:
        return {table.name: [dict(row) for row in connection.execute(select(table)).mappings()]
                for table in (db.product_models, db.option_groups, db.options, db.compatibility_rules, db.product_configs)}


def evaluate(store, model_id, selected):
    if len(selected) != len(set(selected)):
        raise HTTPException(422, "Duplicate option")
    with store.transaction() as connection:
        model = connection.scalar(select(db.product_models.c.id).where(db.product_models.c.id == model_id))
        if not model:
            raise HTTPException(404, "Model not found")
        groups = connection.execute(select(db.option_groups).where(db.option_groups.c.model_id == model_id)).mappings().all()
        options = connection.execute(select(db.options).where(db.options.c.group_id.in_([row["id"] for row in groups]))).mappings().all()
        known = {option["id"] for option in options}
        if not set(selected) <= known:
            raise HTTPException(422, "Unknown option for model")
        errors = []
        for group in groups:
            count = sum(option["id"] in selected for option in options if option["group_id"] == group["id"])
            if not group["minimum"] <= count <= group["maximum"]:
                errors.append(f'{group["id"]} requires {group["minimum"]}..{group["maximum"]} options')
        for rule in connection.execute(select(db.compatibility_rules)).mappings():
            if rule["option_id"] in selected:
                if rule["kind"] == "requires" and rule["other_option_id"] not in selected:
                    errors.append(f'{rule["option_id"]} requires {rule["other_option_id"]}')
                if rule["kind"] == "excludes" and rule["other_option_id"] in selected:
                    errors.append(f'{rule["option_id"]} excludes {rule["other_option_id"]}')
        if errors:
            return {"valid": False, "errors": errors, "bom": [], "synthetic_cost_assumptions": True}
        quantities = defaultdict(int)
        for item in connection.execute(select(db.config_bom).where(db.config_bom.c.model_id == model_id)).mappings():
            if item["option_id"] is None or item["option_id"] in selected:
                quantities[item["part_id"]] += item["qty"]
        items = []
        component_rows = connection.execute(select(db.parts.c.id, db.parts.c.unit_cost,
            db.lead_time_params.c.mean_months).outerjoin(db.lead_time_params,
                db.parts.c.id == db.lead_time_params.c.part_id).where(db.parts.c.id.in_(quantities))).mappings().all()
        components = {row['id']: row for row in component_rows}
        for part_id, qty in sorted(quantities.items()):
            part = components.get(part_id)
            if part is None or part['mean_months'] is None:
                raise HTTPException(422, "Component cost or lead-time data is incomplete")
            items.append({"part_id": part_id, "quantity": qty, "cost_usd": float(part["unit_cost"]) * qty,
                          "lead_months": part['mean_months']})
    return {"valid": True, "errors": [], "bom": items, "cost_usd": sum(item["cost_usd"] for item in items),
            "lead_months": max((item["lead_months"] for item in items), default=0),
            "lead_assumption": "parallel procurement: maximum component lead time", "synthetic_cost_assumptions": True}


def impact(store, model_id, before_options, after_options):
    before = evaluate(store, model_id, before_options)
    after = evaluate(store, model_id, after_options)
    if not before["valid"] or not after["valid"]:
        return {"valid": False, "before": before, "after": after,
                "notice": "Both configurations must be valid before comparing costs or lead times.",
                "synthetic_cost_assumptions": True}
    old = {part["part_id"]: part["quantity"] for part in before["bom"]}
    new = {part["part_id"]: part["quantity"] for part in after["bom"]}
    return {"valid": True, "before": before, "after": after,
            "cost_change_usd": after["cost_usd"] - before["cost_usd"],
            "lead_change_months": after["lead_months"] - before["lead_months"],
            "component_changes": [{"part_id": key, "before_quantity": old.get(key, 0),
                "after_quantity": new.get(key, 0), "quantity_change": new.get(key, 0) - old.get(key, 0)}
                for key in sorted(old.keys() | new.keys()) if old.get(key, 0) != new.get(key, 0)],
            "synthetic_cost_assumptions": True}


def pooling(store):
    configs = catalog(store)["product_configs"]
    appearances = defaultdict(int)
    for config in configs:
        result = evaluate(store, config["model_id"], config["option_ids"])
        for part in result["bom"]:
            appearances[part["part_id"]] += 1
    return {"assumption": "Independent equal-variance configuration demand; theoretical safety-stock reduction, not measured savings.",
            "parts": [{"part_id": part, "configuration_count": count, "commonality": count / len(configs),
                       "safety_stock_reduction_fraction": 1 - 1 / math.sqrt(count)} for part, count in appearances.items()],
            "synthetic_cost_assumptions": True}
