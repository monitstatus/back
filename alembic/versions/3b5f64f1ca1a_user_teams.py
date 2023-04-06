"""User teams

Revision ID: 3b5f64f1ca1a
Revises: 99cb4b41d1f0
Create Date: 2022-10-09 21:18:56.251363

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3b5f64f1ca1a'
down_revision = '99cb4b41d1f0'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('team',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_team_id'), 'team', ['id'], unique=False)
    op.create_index(op.f('ix_team_name'), 'team', ['name'], unique=True)
    op.add_column('user', sa.Column('team_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'user', 'team', ['team_id'], ['id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'user', type_='foreignkey')
    op.drop_column('user', 'team_id')
    op.drop_index(op.f('ix_team_name'), table_name='team')
    op.drop_index(op.f('ix_team_id'), table_name='team')
    op.drop_table('team')
    # ### end Alembic commands ###
