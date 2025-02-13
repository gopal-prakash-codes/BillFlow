"""Added invoice invoice_upload_count and  last_invoice_upload_month fields

Revision ID: e4cc6b94f14a
Revises: 62ab1d7fdb39
Create Date: 2022-07-22 09:43:51.776198

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e4cc6b94f14a'
down_revision = '62ab1d7fdb39'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('upload_invoice_count', sa.Integer(), nullable=True))
    op.add_column('users', sa.Column('last_invoice_upload_month', sa.Integer(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('users', 'last_invoice_upload_month')
    op.drop_column('users', 'upload_invoice_count')
    # ### end Alembic commands ###
