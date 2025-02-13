"""updated invoice table

Revision ID: 16b59b9148ec
Revises: 47a074fc91b8
Create Date: 2023-03-07 11:00:35.322928

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '16b59b9148ec'
down_revision = '47a074fc91b8'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("invoices", sa.Column("attachment", sa.String(), nullable=True))


def downgrade():
    op.drop_column("invoices", "attachment")
