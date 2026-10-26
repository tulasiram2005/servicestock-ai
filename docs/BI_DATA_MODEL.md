# BI data model

PostgreSQL is default. Export public/synthetic parts, locations, suppliers, demand_history and
purchase_orders using python -m app.export. CSV and Parquet share column names. Demand key:
(part_id, location_id, period). Part joins supplier_id to suppliers.id. POs join part_id to parts.id.
Costs are USD and synthetic; periods are YYYY-MM. CSV formula-like strings are escaped.

Exports also include warehouse_inventory, warehouse_sales, product_models, config_bom,
kpi_scorecard and monthly_finance. A manifest records row counts and synthetic labels.
Exports fail above the row cap instead of silently truncating. Parquet is written from typed
rows directly so identifiers and decimal prices are not inferred through a CSV round trip.

## SAP-style synthetic mappings

| Extract family | Fields | Clean destination / use |
|---|---|---|
| MARA | MATNR, MAKTX, MATKL | parts dimension identity, description, category |
| MARC | MATNR, WERKS, PLIFZ | warehouse_inventory lead_days |
| MARD | MATNR, WERKS, LGORT, LABST | warehouse_inventory quantity by part/location |
| MBEW | MATNR, BWKEY, STPRS | warehouse_inventory standard_price |
| EKKO / EKPO | EBELN, BEDAT, MATNR, MENGE, NETPR | synthetic extracts from purchase_orders; reverse import pending |
| VBAK / VBAP | VBELN, AUDAT, MATNR, WERKS, KWMENG | warehouse_sales fact joined to part/location |
| STKO / STPO | STLNR, MODEL, OPTION, IDNRK, MENGE | synthetic extracts from config_bom; reverse import pending |

All ten families are generated deterministically into the logical staging_extracts namespace.
Inventory and sales facts are transactionally rebuilt from those extracts. No real SAP system
was used; this is not SAP-certified integration. A physically separate staging schema and full
reverse import of purchase/BOM extracts are not implemented. SQL Server DDL compilation passes;
runtime compatibility has not been measured.
