"""initial models

Revision ID: 9d261f4ad8a2
Revises:
Create Date: 2022-03-05 20:13:06.350507

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "9d261f4ad8a2"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "organizations",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=True),
        sa.Column("address", sa.String(), nullable=True),
        sa.Column("legal_business_type", sa.String(), nullable=True),
        sa.Column(
            "created_on", sa.DateTime(), server_default=sa.text("now()"), nullable=True
        ),
        sa.Column("updated_on", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "vendors",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=True),
        sa.Column("aliases", sa.ARRAY(sa.String()), nullable=True),
        sa.Column("contact_email", sa.String(), nullable=True),
        sa.Column(
            "created_on", sa.DateTime(), server_default=sa.text("now()"), nullable=True
        ),
        sa.Column("updated_on", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "users",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("organization_id", sa.String(), nullable=True),
        sa.Column("paid_plan", sa.String(), nullable=True),
        sa.Column("stripe_session_id", sa.String(), nullable=True),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("password_hash", sa.String(), nullable=False),
        sa.Column(
            "created_on", sa.DateTime(), server_default=sa.text("now()"), nullable=True
        ),
        sa.Column("updated_on", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_table(
        "invoices",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=True),
        sa.Column("organization_id", sa.String(), nullable=True),
        sa.Column("vendor_id", sa.String(), nullable=True),
        sa.Column("is_paid", sa.Boolean(), nullable=True),
        sa.Column("vendor_name", sa.String(), nullable=True),
        sa.Column("amount_due", sa.DECIMAL(), nullable=True),
        sa.Column("currency", sa.String(), nullable=True),
        sa.Column("due_date", sa.DateTime(), nullable=True),
        sa.Column("invoice_id", sa.String(), nullable=True),
        sa.Column("raw_vendor_name", sa.String(), nullable=True),
        sa.Column("raw_amount_due", sa.String(), nullable=True),
        sa.Column("raw_due_date", sa.String(), nullable=True),
        sa.Column(
            "created_on", sa.DateTime(), server_default=sa.text("now()"), nullable=True
        ),
        sa.Column("updated_on", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.ForeignKeyConstraint(
            ["vendor_id"],
            ["vendors.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_invoices_organization_id"),
        "invoices",
        ["organization_id"],
        unique=False,
    )
    op.create_index(op.f("ix_invoices_user_id"), "invoices", ["user_id"], unique=False)
    op.create_index(
        op.f("ix_invoices_vendor_id"), "invoices", ["vendor_id"], unique=False
    )
    op.create_table(
        "reset_password_tokens",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("token", sa.String(), nullable=False),
        sa.Column(
            "created_on", sa.DateTime(), server_default=sa.text("now()"), nullable=True
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("reset_password_tokens")
    op.drop_index(op.f("ix_invoices_vendor_id"), table_name="invoices")
    op.drop_index(op.f("ix_invoices_user_id"), table_name="invoices")
    op.drop_index(op.f("ix_invoices_organization_id"), table_name="invoices")
    op.drop_table("invoices")
    op.drop_table("users")
    op.drop_table("vendors")
    op.drop_table("organizations")
    # ### end Alembic commands ###
