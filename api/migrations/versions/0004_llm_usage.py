from alembic import op
import sqlalchemy as sa

revision = '0004'
down_revision = '0003'


def upgrade():
    op.create_table('llm_daily_usage', sa.Column('day', sa.Integer(), primary_key=True),
        sa.Column('subject', sa.String(64), primary_key=True),
        sa.Column('attempts', sa.Integer(), nullable=False))


def downgrade():
    op.drop_table('llm_daily_usage')
