from decimal import Decimal
import hashlib
import json
import math
from datetime import datetime

from sqlalchemy import select, delete

from app.db import schema as db

LABEL = "SAP-style synthetic extract; no SAP system was used."


def generate_and_transform(store):
    with store.transaction() as connection:
        parts = connection.execute(select(db.parts).order_by(db.parts.c.id)).mappings().all()
        orders = connection.execute(select(db.purchase_orders).order_by(db.purchase_orders.c.id)).mappings().all()
        bom = connection.execute(select(db.config_bom).order_by(db.config_bom.c.id)).mappings().all()
        lead = dict(connection.execute(select(db.lead_time_params.c.part_id, db.lead_time_params.c.mean_months)).all())
        models = set(connection.scalars(select(db.product_models.c.id)))
        option_models = dict(connection.execute(select(db.options.c.id, db.option_groups.c.model_id).join(
            db.option_groups, db.options.c.group_id == db.option_groups.c.id)).all())
    extracts = []
    def add(table, key, payload):
        extracts.append({"id": table + ":" + key, "sap_table": table, "payload": payload, "label": LABEL})
    for index, part in enumerate(parts):
        part_id = part["id"]
        add("MARA", part_id, {"MATNR": part_id, "MAKTX": part["description"], "MATKL": part["category"]})
        add("MARC", part_id, {"MATNR": part_id, "WERKS": "LOC-1", "PLIFZ": lead[part_id] * 30})
        add("MARD", part_id, {"MATNR": part_id, "WERKS": "LOC-1", "LGORT": "DEMO", "LABST": 10 + index})
        add("MBEW", part_id, {"MATNR": part_id, "BWKEY": "LOC-1", "STPRS": str(part["unit_cost"])})
    for order in orders:
        add("EKKO", order["id"], {"EBELN": order["id"], "BEDAT": order["period"], "WAERS": "USD"})
        add("EKPO", order["id"], {"EBELN": order["id"], "EBELP": "10", "MATNR": order["part_id"],
                                  "MENGE": order["qty"], "NETPR": str(order["actual_price"]),
                                  "Z_STANDARD_PRICE": str(order["standard_price"]), "Z_BUDGET": str(order["budget"]),
                                  "Z_EXPEDITE_SPEND": str(order["expedite_spend"])})
        add("VBAK", order["id"], {"VBELN": "SO-" + order["id"], "AUDAT": order["period"]})
        add("VBAP", order["id"], {"VBELN": "SO-" + order["id"], "POSNR": "10", "MATNR": order["part_id"],
                                  "WERKS": "LOC-1", "KWMENG": order["qty"]})
    for item in bom:
        add("STKO", item["id"], {"STLNR": item["id"], "MODEL": item["model_id"], "OPTION": item["option_id"]})
        add("STPO", item["id"], {"STLNR": item["id"], "IDNRK": item["part_id"], "MENGE": item["qty"]})
    inventories, sales = transform(extracts, {part["id"] for part in parts})
    purchases, components = transform_purchase_bom(extracts, {part["id"] for part in parts}, models, option_models)
    with store.transaction() as connection:
        connection.execute(delete(db.staging_extracts))
        connection.execute(delete(db.warehouse_inventory))
        connection.execute(delete(db.warehouse_sales))
        connection.execute(delete(db.purchase_orders))
        connection.execute(delete(db.config_bom))
        if extracts:
            connection.execute(db.staging_extracts.insert(), extracts)
        if inventories:
            connection.execute(db.warehouse_inventory.insert(), inventories)
        if sales:
            connection.execute(db.warehouse_sales.insert(), sales)
        if purchases:
            connection.execute(db.purchase_orders.insert(), purchases)
        if components:
            connection.execute(db.config_bom.insert(), components)
    return {"label": LABEL, "tables": sorted({row["sap_table"] for row in extracts}), "extract_rows": len(extracts),
            "inventory_rows": len(inventories), "sales_rows": len(sales),
            "purchase_rows": len(purchases), "bom_rows": len(components),
            "sha256": hashlib.sha256(json.dumps(extracts, sort_keys=True).encode()).hexdigest()}


def transform(extracts, valid_parts):
    grouped = {}
    for row in extracts:
        grouped.setdefault(row["sap_table"], []).append(row["payload"])
    costs = {(row["MATNR"], row["BWKEY"]): Decimal(row["STPRS"]) for row in grouped.get("MBEW", [])}
    leads = {(row["MATNR"], row["WERKS"]): float(row["PLIFZ"]) for row in grouped.get("MARC", [])}
    periods = {row["VBELN"]: row["AUDAT"] for row in grouped.get("VBAK", [])}
    def nonnegative(value):
        converted = float(value)
        if not math.isfinite(converted) or converted < 0:
            raise ValueError("Staging numbers must be finite and nonnegative")
        return converted

    for value in costs.values():
        nonnegative(value)
    for value in leads.values():
        nonnegative(value)
    for value in periods.values():
        if datetime.strptime(value, "%Y-%m").strftime("%Y-%m") != value:
            raise ValueError("Invalid staging period")
    inventory, sales = [], []
    inventory_keys, sales_keys = set(), set()
    for row in grouped.get("MARD", []):
        key = (row["MATNR"], row["WERKS"])
        if key[0] not in valid_parts or key not in costs or key not in leads:
            raise ValueError("Invalid staging inventory reference or quantity")
        if key in inventory_keys:
            raise ValueError("Duplicate staging inventory key; aggregate storage locations before import")
        inventory_keys.add(key)
        inventory.append({"part_id": key[0], "location_id": key[1], "quantity": nonnegative(row["LABST"]),
                          "standard_price": costs[key], "lead_days": leads[key]})
    for row in grouped.get("VBAP", []):
        if row["MATNR"] not in valid_parts or row["VBELN"] not in periods or (row["MATNR"], row["WERKS"]) not in leads:
            raise ValueError("Invalid staging sales reference or quantity")
        key = row["VBELN"] + ":" + row["POSNR"]
        if key in sales_keys:
            raise ValueError("Duplicate staging sales key")
        sales_keys.add(key)
        sales.append({"id": key, "part_id": row["MATNR"],
                      "location_id": row["WERKS"], "period": periods[row["VBELN"]], "quantity": nonnegative(row["KWMENG"])})
    return inventory, sales


def transform_purchase_bom(extracts, valid_parts, valid_models, option_models):
    """Import the documented single-line synthetic order/BOM extract contract."""
    grouped = {}
    for row in extracts:
        grouped.setdefault(row["sap_table"], []).append(row["payload"])

    def unique_index(family, key):
        result = {}
        for row in grouped.get(family, []):
            if row[key] in result:
                raise ValueError("Duplicate staging header")
            result[row[key]] = row
        return result

    def money(value):
        amount = Decimal(str(value))
        if not amount.is_finite() or amount < 0 or amount >= Decimal('1000000000000') or amount != amount.quantize(Decimal('0.01')):
            raise ValueError("Invalid staging monetary value")
        return amount

    def quantity(value):
        number = Decimal(str(value))
        if not number.is_finite() or number <= 0 or number != number.to_integral_value() or number > 2147483647:
            raise ValueError("Staging quantity must be a positive bounded integer")
        return int(number)

    orders, headers = unique_index('EKKO', 'EBELN'), unique_index('STKO', 'STLNR')
    purchases, components = [], []
    seen_orders, seen_bom = set(), set()
    for row in grouped.get('EKPO', []):
        key = row['EBELN']
        if key not in orders or row['MATNR'] not in valid_parts or key in seen_orders:
            raise ValueError('Invalid or duplicate staging purchase reference')
        header = orders[key]
        period = header['BEDAT']
        if datetime.strptime(period, '%Y-%m').strftime('%Y-%m') != period or header['WAERS'] != 'USD':
            raise ValueError('Invalid staging purchase period or currency')
        seen_orders.add(key)
        purchases.append({'id': key, 'part_id': row['MATNR'], 'period': period, 'qty': quantity(row['MENGE']),
            'actual_price': money(row['NETPR']), 'standard_price': money(row['Z_STANDARD_PRICE']),
            'budget': money(row['Z_BUDGET']), 'expedite_spend': money(row['Z_EXPEDITE_SPEND'])})
    for row in grouped.get('STPO', []):
        key = row['STLNR']
        if key not in headers or row['IDNRK'] not in valid_parts or key in seen_bom:
            raise ValueError('Invalid or duplicate staging BOM reference')
        header = headers[key]
        model, option = header['MODEL'], header['OPTION']
        if model not in valid_models or (option is not None and option_models.get(option) != model):
            raise ValueError('Invalid staging model or option reference')
        seen_bom.add(key)
        components.append({'id': key, 'model_id': model, 'option_id': option,
            'part_id': row['IDNRK'], 'qty': quantity(row['MENGE'])})
    if seen_orders != orders.keys() or seen_bom != headers.keys():
        raise ValueError('Staging header has no detail row')
    return purchases, components
