"""added fields customer_id, plan_strted, plan_expiry and plan_id in users table

Revision ID: 62ab1d7fdb39
Revises: e679b059e655
Create Date: 2022-07-13 13:22:47.178666

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "62ab1d7fdb39"
down_revision = "e679b059e655"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("users", sa.Column("customer_id", sa.String(), nullable=True))
    op.add_column("users", sa.Column("plan_started", sa.DateTime(), nullable=True))
    op.add_column("users", sa.Column("plan_expiry", sa.DateTime(), nullable=True))
    op.add_column("users", sa.Column("plan_id", sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("users", "plan_id")
    op.drop_column("users", "plan_expiry")
    op.drop_column("users", "plan_started")
    op.drop_column("users", "customer_id")
    # ### end Alembic commands ###
