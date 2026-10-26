# BI data model

PostgreSQL is default. Export public/synthetic parts, locations, suppliers, demand_history and
purchase_orders using python -m app.export. CSV and Parquet share column names. Demand key:
(part_id, location_id, period). Part joins supplier_id to suppliers.id. POs join part_id to parts.id.
Costs are USD and synthetic; periods are YYYY-MM. CSV formula-like strings are escaped.

Current export covers these five tables; normalized KPI fact exports and a full star-schema
warehouse view set remain pending. SQL Server DDL compilation passes; runtime compatibility
has not been measured. No SAP system was used. Staging rows currently mimic MARA/MBEW only;
the full MARC/MARD/EKKO/EKPO/VBAK/VBAP/STKO/STPO ETL mapping is incomplete.
