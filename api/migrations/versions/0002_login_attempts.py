from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"


def upgrade():
    op.create_table("login_attempts", sa.Column("id", sa.String(64), primary_key=True),
                    sa.Column("failures", sa.Integer(), nullable=False),
                    sa.Column("locked_until", sa.Float(), nullable=False))


def downgrade():
    op.drop_table("login_attempts")
