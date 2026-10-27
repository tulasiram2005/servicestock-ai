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
| EKKO / EKPO | EBELN, BEDAT, MATNR, MENGE, NETPR | purchase_orders, validated header/detail import |
| VBAK / VBAP | VBELN, AUDAT, MATNR, WERKS, KWMENG | warehouse_sales fact joined to part/location |
| STKO / STPO | STLNR, MODEL, OPTION, IDNRK, MENGE | config_bom, validated model/option/component import |

All ten families are generated into typed tables in the physical `staging` schema on
PostgreSQL and SQL Server: mara, marc, mard, mbew, ekko, ekpo, vbak, vbap, stko, stpo.
SAP-style field names are retained as columns, with decimal prices and a synthetic label.
SQLite maps the namespace to its main database for offline tests. The legacy JSON
`staging_extracts` table remains available for compatibility. Inventory, sales, purchase
and BOM records are read back from typed staging and rebuilt in the same transaction.
Purchase finance fields use explicitly synthetic extensions Z_STANDARD_PRICE, Z_BUDGET and
Z_EXPEDITE_SPEND. The demo format has one detail per purchase/BOM header; duplicate details
are rejected rather than overwritten. USD only; quantities are positive bounded integers,
prices nonnegative finite decimals with at most two fractional digits. Options must belong
to the referenced model. Any validation or insertion failure rolls back staging and warehouse changes together.

No real SAP system was used; this is not SAP-certified integration. General external SAP import and external uploads are not implemented.
SQL Server DDL compilation passes; the new staging tables have not been runtime-tested
on SQL Server. Targeted queue/quota/refresh SQL Server tests passed before this migration.

## Multi-line synthetic purchase and BOM mapping

EKPO details use EBELN + EBELP; STPO details use STLNR + POSNR. Line numbers are positive
ASCII integers up to six digits; leading zeros normalize before duplicate detection.
Legacy line 10 (or an omitted line number) preserves the header ID; other lines use
`header:line`. IDs over 64 characters or collisions are rejected. Each header must have
a detail. Existing money, currency, period, quantity and reference validation still applies.
Budget and expedite fields are per-detail values, never repeated header totals.
This extends the transformation functions, not a general external SAP import endpoint.
The local generator still produces single-line fixtures. SAP-style synthetic extract;
no SAP system was used. Migration 0005 preserves legacy history; the next synthetic ETL populates typed tables.
Downgrade removes only the ten typed tables, retaining legacy history and the schema namespace.
Local PostgreSQL migration and repeated ETL passed with 1,258 typed rows.
