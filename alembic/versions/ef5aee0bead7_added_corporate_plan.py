"""added_corporate_plan

Revision ID: ef5aee0bead7
Revises: ef0c2e70b1e4
Create Date: 2023-12-14 14:30:37.330078

"""
from alembic import op
import sqlalchemy as sa

import ulid


# revision identifiers, used by Alembic.
revision = 'ef5aee0bead7'
down_revision = 'ef0c2e70b1e4'
branch_labels = None
depends_on = None
environment = "production"


def upgrade():
    if environment == "development":
        op.execute("""
        INSERT INTO plans (
            id,
            product_type,
            stripe_plan_id,
            plan_key,
            plan_description,
            included_features,
            plan_price,
            max_approvers_raw
        ) VALUES (
            '{id}',
            '{product_type}',
            '{stripe_plan_id}',
            '{plan_key}',
            '{plan_description}',
            '{included_features}',
            '{plan_price}',
            '{max_approvers_raw}'
        )
        """.format(
            id=ulid.ulid(),
            product_type='user_subscription',
            stripe_plan_id='price_1ONEnhE0SvQaZIgKR2z8oI0b',
            plan_key='Corporate',
            plan_description='Elevate Your Corporate Finances: Seamless Invoice Management for Limitless Growth.',
            included_features='Unlimited invoices;Unlimited users;Unlimited approvers;',
            plan_price='99',
            max_approvers_raw='Unlimited'
        ))
    else:
        # production upgrade
        op.execute("""
        INSERT INTO plans (
            id,
            product_type,
            stripe_plan_id,
            plan_key,
            plan_description,
            included_features,
            plan_price,
            max_approvers_raw
        ) VALUES (
            '{id}',
            '{product_type}',
            '{stripe_plan_id}',
            '{plan_key}',
            '{plan_description}',
            '{included_features}',
            '{plan_price}',
            '{max_approvers_raw}'
        )
        """.format(
            id=ulid.ulid(),
            product_type='user_subscription',
            stripe_plan_id='price_1OOynhE0SvQaZIgKdd8GlS5m',
            plan_key='Corporate',
            plan_description='Elevate Your Corporate Finances: Seamless Invoice Management for Limitless Growth.',
            included_features='Unlimited invoices;Unlimited users;Unlimited approvers;',
            plan_price='99',
            max_approvers_raw='Unlimited'
        ))


def downgrade():
    if environment == "development":
        op.execute("DELETE FROM plans WHERE stripe_plan_id = 'price_1ONEnhE0SvQaZIgKR2z8oI0b'")
    else:
        op.execute("DELETE FROM plans WHERE stripe_plan_id = 'price_1OOynhE0SvQaZIgKdd8GlS5m'")
