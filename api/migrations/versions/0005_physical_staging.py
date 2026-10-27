"""Add typed staging tables without removing legacy extract history."""
from alembic import op
import sqlalchemy as sa
from migrations.staging_v5 import define_tables

revision = '0005'
down_revision = '0004'


def upgrade():
    metadata = sa.MetaData()
    define_tables(metadata)
    metadata.create_all(op.get_bind())
    # Existing generic JSON history stays untouched. The next synthetic ETL populates
    # typed landing tables atomically alongside the warehouse, after validation.


def downgrade():
    metadata = sa.MetaData()
    define_tables(metadata)
    metadata.drop_all(op.get_bind())
    # Keep the namespace: other user-managed objects may exist in it.
