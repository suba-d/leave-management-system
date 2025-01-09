"""add com

Revision ID: 9d0e455da701
Revises: 4ce50908caac
Create Date: 2025-01-09 11:10:48.801556

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9d0e455da701'
down_revision = '4ce50908caac'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('compassionate_days', sa.Float(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_column('compassionate_days')

    # ### end Alembic commands ###
