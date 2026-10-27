import os
from alembic import context
from sqlalchemy import create_engine, pool
from app.db.schema import metadata

engine = create_engine(os.environ["DATABASE_URL"], poolclass=pool.NullPool, hide_parameters=True)
if engine.dialect.name == "sqlite":
    engine = engine.execution_options(schema_translate_map={"staging": None})
with engine.connect() as connection:
    context.configure(connection=connection, target_metadata=metadata, compare_type=True)
    with context.begin_transaction():
        context.run_migrations()
