from decimal import Decimal
import hashlib
import json

from sqlalchemy import select, delete

from app.db import schema as db

LABEL = "SAP-style synthetic extract; no SAP system was used."


def generate_and_transform(store):
    with store.transaction() as connection:
        parts = connection.execute(select(db.parts).order_by(db.parts.c.id)).mappings().all()
        orders = connection.execute(select(db.purchase_orders).order_by(db.purchase_orders.c.id)).mappings().all()
        bom = connection.execute(select(db.config_bom).order_by(db.config_bom.c.id)).mappings().all()
        lead = dict(connection.execute(select(db.lead_time_params.c.part_id, db.lead_time_params.c.mean_months)).all())
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
                                  "MENGE": order["qty"], "NETPR": str(order["actual_price"])})
        add("VBAK", order["id"], {"VBELN": "SO-" + order["id"], "AUDAT": order["period"]})
        add("VBAP", order["id"], {"VBELN": "SO-" + order["id"], "POSNR": "10", "MATNR": order["part_id"],
                                  "WERKS": "LOC-1", "KWMENG": order["qty"]})
    for item in bom:
        add("STKO", item["id"], {"STLNR": item["id"], "MODEL": item["model_id"], "OPTION": item["option_id"]})
        add("STPO", item["id"], {"STLNR": item["id"], "IDNRK": item["part_id"], "MENGE": item["qty"]})
    inventories, sales = transform(extracts, {part["id"] for part in parts})
    with store.transaction() as connection:
        connection.execute(delete(db.staging_extracts))
        connection.execute(delete(db.warehouse_inventory))
        connection.execute(delete(db.warehouse_sales))
        if extracts:
            connection.execute(db.staging_extracts.insert(), extracts)
        if inventories:
            connection.execute(db.warehouse_inventory.insert(), inventories)
        if sales:
            connection.execute(db.warehouse_sales.insert(), sales)
    return {"label": LABEL, "tables": sorted({row["sap_table"] for row in extracts}), "extract_rows": len(extracts),
            "inventory_rows": len(inventories), "sales_rows": len(sales),
            "sha256": hashlib.sha256(json.dumps(extracts, sort_keys=True).encode()).hexdigest()}


def transform(extracts, valid_parts):
    grouped = {}
    for row in extracts:
        grouped.setdefault(row["sap_table"], []).append(row["payload"])
    costs = {(row["MATNR"], row["BWKEY"]): Decimal(row["STPRS"]) for row in grouped.get("MBEW", [])}
    leads = {(row["MATNR"], row["WERKS"]): float(row["PLIFZ"]) for row in grouped.get("MARC", [])}
    periods = {row["VBELN"]: row["AUDAT"] for row in grouped.get("VBAK", [])}
    inventory, sales = [], []
    for row in grouped.get("MARD", []):
        key = (row["MATNR"], row["WERKS"])
        if key[0] not in valid_parts or key not in costs or key not in leads or float(row["LABST"]) < 0:
            raise ValueError("Invalid staging inventory reference or quantity")
        inventory.append({"part_id": key[0], "location_id": key[1], "quantity": float(row["LABST"]),
                          "standard_price": costs[key], "lead_days": leads[key]})
    for row in grouped.get("VBAP", []):
        if row["MATNR"] not in valid_parts or row["VBELN"] not in periods or float(row["KWMENG"]) < 0:
            raise ValueError("Invalid staging sales reference or quantity")
        sales.append({"id": row["VBELN"] + ":" + row["POSNR"], "part_id": row["MATNR"],
                      "location_id": row["WERKS"], "period": periods[row["VBELN"]], "quantity": float(row["KWMENG"])})
    return inventory, sales
