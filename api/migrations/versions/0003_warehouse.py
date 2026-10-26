from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"


def upgrade():
    op.create_table("warehouse_inventory",
        sa.Column("part_id", sa.String(64), sa.ForeignKey("parts.id"), primary_key=True),
        sa.Column("location_id", sa.String(64), sa.ForeignKey("locations.id"), primary_key=True),
        sa.Column("quantity", sa.Float(), nullable=False), sa.Column("standard_price", sa.Numeric(14, 2), nullable=False),
        sa.Column("lead_days", sa.Float(), nullable=False))
    op.create_table("warehouse_sales", sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("part_id", sa.String(64), sa.ForeignKey("parts.id"), nullable=False),
        sa.Column("location_id", sa.String(64), sa.ForeignKey("locations.id"), nullable=False),
        sa.Column("period", sa.String(7), nullable=False), sa.Column("quantity", sa.Float(), nullable=False))


def downgrade():
    op.drop_table("warehouse_sales")
    op.drop_table("warehouse_inventory")
