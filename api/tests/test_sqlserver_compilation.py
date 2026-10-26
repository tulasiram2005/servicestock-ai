"""Offline dialect checks; these do not claim SQL Server runtime compatibility."""
from sqlalchemy import create_mock_engine, select, update
from sqlalchemy.dialects import mssql
from app.db import schema as db


def test_entire_schema_compiles_for_sqlserver():
    statements = []
    dialect = mssql.dialect()
    engine = create_mock_engine('mssql+pyodbc://', lambda statement, *a, **kw: statements.append(str(statement.compile(dialect=dialect))))
    db.metadata.create_all(engine)
    for table in db.metadata.tables:
        assert any('CREATE TABLE '+table+' ' in statement or 'CREATE TABLE '+table+' (' in statement for statement in statements), table
    assert any('NVARCHAR(max)' in statement for statement in statements)


def test_sqlserver_queue_lock_and_account_update_compile():
    query = select(db.jobs).where(db.jobs.c.status == 'pending').order_by(db.jobs.c.created_at,db.jobs.c.id).limit(1)
    query = query.with_hint(db.jobs,'WITH (UPDLOCK, READPAST, ROWLOCK)',dialect_name='mssql')
    sql = str(query.compile(dialect=mssql.dialect(),compile_kwargs={'literal_binds':True}))
    assert 'TOP 1' in sql
    assert 'WITH (UPDLOCK, READPAST, ROWLOCK)' in sql
    assert 'FOR UPDATE' not in sql
    locked = update(db.users).where(db.users.c.id == 'probe').values(id=db.users.c.id)
    assert 'SET id=users.id' in str(locked.compile(dialect=mssql.dialect()))
