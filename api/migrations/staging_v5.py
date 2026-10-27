"""Typed SAP-style synthetic landing tables; no SAP connection is used."""
from sqlalchemy import Table, Column, String, Float, Numeric, DDL, event


def define_tables(metadata):
    fields = {
        'MARA': {'MATNR': String(64), 'MAKTX': String(240), 'MATKL': String(30)},
        'MARC': {'MATNR': String(64), 'WERKS': String(64), 'PLIFZ': Float()},
        'MARD': {'MATNR': String(64), 'WERKS': String(64), 'LGORT': String(64), 'LABST': Float()},
        'MBEW': {'MATNR': String(64), 'BWKEY': String(64), 'STPRS': Numeric(14,2)},
        'EKKO': {'EBELN': String(64), 'BEDAT': String(7), 'WAERS': String(3)},
        'EKPO': {'EBELN': String(64), 'EBELP': String(6), 'MATNR': String(64), 'MENGE': Float(), 'NETPR': Numeric(14,2), 'Z_STANDARD_PRICE': Numeric(14,2), 'Z_BUDGET': Numeric(14,2), 'Z_EXPEDITE_SPEND': Numeric(14,2)},
        'VBAK': {'VBELN': String(64), 'AUDAT': String(7)},
        'VBAP': {'VBELN': String(64), 'POSNR': String(6), 'MATNR': String(64), 'WERKS': String(64), 'KWMENG': Float()},
        'STKO': {'STLNR': String(64), 'MODEL': String(64), 'OPTION': String(64)},
        'STPO': {'STLNR': String(64), 'POSNR': String(6), 'IDNRK': String(64), 'MENGE': Float()},
    }
    for ddl,dialect in [("CREATE SCHEMA IF NOT EXISTS staging",'postgresql'),
                        ("IF SCHEMA_ID('staging') IS NULL EXEC('CREATE SCHEMA staging')",'mssql')]:
        event.listen(metadata,'before_create',DDL(ddl).execute_if(dialect=dialect))
    return {name: Table(name.lower(),metadata,Column('extract_id',String(128),primary_key=True),
                *(Column(key,kind,nullable=key in {'OPTION','POSNR'}) for key,kind in columns.items()),
                Column('label',String(100),nullable=False),schema='staging') for name,columns in fields.items()}
