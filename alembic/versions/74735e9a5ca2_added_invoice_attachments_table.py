"""added invoice_attachments_table

Revision ID: 74735e9a5ca2
Revises: 47a074fc91b8
Create Date: 2023-03-09 06:13:01.087086

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '74735e9a5ca2'
down_revision = '16b59b9148ec'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('invoice_attachments',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('invoice_id', sa.String, nullable=False),
    sa.Column('attachment', sa.String(), nullable=False),
    sa.Column('attachment_type', sa.String(), nullable=False),
    sa.Column('created_on', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.ForeignKeyConstraint(['invoice_id'], ['invoices.id']),
    )


def downgrade():
    op.drop_table('invoice_attachments')
