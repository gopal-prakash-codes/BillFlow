"""added_new_plan_and_update_price_for_plans

Revision ID: a65127cc0d90
Revises: 74735e9a5ca2
Create Date: 2023-11-29 08:30:56.839331

"""
from alembic import op
import sqlalchemy as sa
import ulid


# revision identifiers, used by Alembic.
revision = 'a65127cc0d90'
down_revision = '74735e9a5ca2'
branch_labels = None
depends_on = None
environment = "production"

    
def upgrade():
    if environment == "development":
        op.execute("UPDATE plans SET plan_price='15', stripe_plan_id='price_1OHgQsE0SvQaZIgKu0QKM8uJ' WHERE stripe_plan_id ='price_1LmGPwE0SvQaZIgKHB2JjJho'")
        op.execute("UPDATE plans SET plan_price='30', stripe_plan_id='price_1OHgScE0SvQaZIgKiBN2mHq5' WHERE stripe_plan_id ='price_1LmC9XE0SvQaZIgKyQ3NImTY'")
        op.execute("""
            INSERT INTO plans (
                id,
                product_type,
                stripe_plan_id,
                plan_key,
                plan_price,
                max_approvers,
                max_approvers_raw
            ) VALUES (
                '{id}',
                '{product_type}',
                '{stripe_plan_id}',
                '{plan_key}',
                '{plan_price}',
                {max_approvers},
                '{max_approvers_raw}'
            )
        """.format(
            id=ulid.ulid(),
            product_type='approver_subscription',
            stripe_plan_id='price_1OHgV3E0SvQaZIgKyLbT8XQO',
            plan_key='Five Approver',
            plan_price='55',
            max_approvers=5,
            max_approvers_raw='Five'
        ))
    else:
        # producion upgrade
        op.execute("UPDATE plans SET plan_price='15', stripe_plan_id='price_1OHgbcE0SvQaZIgKFT0PNKn7' WHERE stripe_plan_id ='price_1LyyTLE0SvQaZIgKefAbZqfY'")
        op.execute("UPDATE plans SET plan_price='30', stripe_plan_id='price_1OHgc2E0SvQaZIgKDmeBCDJu' WHERE stripe_plan_id ='price_1LyyTLE0SvQaZIgKTusJhKfp'")
        op.execute("""
            INSERT INTO plans (
                id,
                product_type,
                stripe_plan_id,
                plan_key,
                plan_price,
                max_approvers,
                max_approvers_raw
            ) VALUES (
                '{id}',
                '{product_type}',
                '{stripe_plan_id}',
                '{plan_key}',
                '{plan_price}',
                {max_approvers},
                '{max_approvers_raw}'
            )
        """.format(
            id=ulid.ulid(),
            product_type='approver_subscription',
            stripe_plan_id='price_1OHgcoE0SvQaZIgKVxzVqB5H',
            plan_key='Five Approver',
            plan_price='55',
            max_approvers=5,
            max_approvers_raw='Five'
        ))


def downgrade():
    if environment == "development":
        op.execute("UPDATE plans SET plan_price='12', stripe_plan_id='price_1LmGPwE0SvQaZIgKHB2JjJho' WHERE stripe_plan_id ='price_1OHgQsE0SvQaZIgKu0QKM8uJ'")
        op.execute("UPDATE plans SET plan_price='24', stripe_plan_id='price_1LmC9XE0SvQaZIgKyQ3NImTY' WHERE stripe_plan_id ='price_1OHgScE0SvQaZIgKiBN2mHq5'")
        op.execute("DELETE FROM plans WHERE stripe_plan_id = 'price_1OHgV3E0SvQaZIgKyLbT8XQO'")
    else:
        # production downgrade
        op.execute("UPDATE plans SET plan_price='12', stripe_plan_id='price_1LyyTLE0SvQaZIgKefAbZqfY' WHERE stripe_plan_id ='price_1OHgbcE0SvQaZIgKFT0PNKn7'")
        op.execute("UPDATE plans SET plan_price='24', stripe_plan_id='price_1LyyTLE0SvQaZIgKTusJhKfp' WHERE stripe_plan_id ='price_1OHgc2E0SvQaZIgKDmeBCDJu'")
        op.execute("DELETE FROM plans WHERE stripe_plan_id = 'price_1OHgcoE0SvQaZIgKVxzVqB5H'")
