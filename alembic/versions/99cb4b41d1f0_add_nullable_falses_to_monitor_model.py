"""Add nullable falses to monitor model

Revision ID: 99cb4b41d1f0
Revises: 703bd77c5625
Create Date: 2022-10-09 19:06:37.508123

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '99cb4b41d1f0'
down_revision = '703bd77c5625'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('monitor', 'name',
               existing_type=sa.VARCHAR(),
               nullable=False)
    op.alter_column('monitor', 'monitor_type',
               existing_type=sa.VARCHAR(),
               nullable=False)
    op.alter_column('monitor', 'endpoint',
               existing_type=sa.VARCHAR(),
               nullable=False)
    op.alter_column('monitor', 'alert_type',
               existing_type=sa.VARCHAR(),
               nullable=False)
    op.alter_column('monitor', 'periodicity',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('monitor', 'request_timeout',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('user', 'full_name',
               existing_type=sa.VARCHAR(),
               nullable=False)
    op.drop_index('ix_user_full_name', table_name='user')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_index('ix_user_full_name', 'user', ['full_name'], unique=False)
    op.alter_column('user', 'full_name',
               existing_type=sa.VARCHAR(),
               nullable=True)
    op.alter_column('monitor', 'request_timeout',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('monitor', 'periodicity',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('monitor', 'alert_type',
               existing_type=sa.VARCHAR(),
               nullable=True)
    op.alter_column('monitor', 'endpoint',
               existing_type=sa.VARCHAR(),
               nullable=True)
    op.alter_column('monitor', 'monitor_type',
               existing_type=sa.VARCHAR(),
               nullable=True)
    op.alter_column('monitor', 'name',
               existing_type=sa.VARCHAR(),
               nullable=True)
    # ### end Alembic commands ###
