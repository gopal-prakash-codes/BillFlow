"""Fix is_approved null for invoices

Revision ID: a512108ad127
Revises: c3e361c91c8d
Create Date: 2022-11-23 22:45:47.437122

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a512108ad127'
down_revision = 'c3e361c91c8d'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""update invoices set is_approved = false where is_approved is null""")


def downgrade():
    pass
