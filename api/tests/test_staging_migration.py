import os
from pathlib import Path
import subprocess
import sys
from sqlalchemy import create_engine, inspect, text


def test_existing_database_upgrade_downgrade_preserves_legacy_rows(tmp_path):
    api = Path(__file__).resolve().parents[1]
    url = 'sqlite:///' + str(tmp_path/'migration.db')
    env = {**os.environ, 'DATABASE_URL':url, 'PYTHONPATH':str(api)}
    def migrate(*args):
        subprocess.run([sys.executable,'-m','alembic',*args],cwd=api,env=env,check=True,capture_output=True)
    migrate('upgrade','0004')
    engine = create_engine(url)
    with engine.begin() as connection:
        connection.execute(text("INSERT INTO staging_extracts (id,sap_table,payload,label) VALUES ('legacy','MARA','{}','preserve')"))
    migrate('upgrade','head')
    assert {'mara','marc','mard','mbew','ekko','ekpo','vbak','vbap','stko','stpo'} <= set(inspect(engine).get_table_names())
    migrate('downgrade','0004')
    assert 'mara' not in inspect(engine).get_table_names()
    with engine.connect() as connection:
        assert connection.scalar(text('SELECT label FROM staging_extracts')) == 'preserve'
    migrate('upgrade','head')
    engine.dispose()
