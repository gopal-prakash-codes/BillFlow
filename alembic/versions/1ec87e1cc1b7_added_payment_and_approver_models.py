"""added payment and approver models

Revision ID: 1ec87e1cc1b7
Revises: 54851f4cbe99
Create Date: 2022-10-29 11:50:16.547918

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column

import ulid


# revision identifiers, used by Alembic.
revision = '1ec87e1cc1b7'
down_revision = '54851f4cbe99'
branch_labels = None
depends_on = None
environment = "production"

if environment == "development":
    INITIAL_DATA = {
        'products': [
            {
                'id': ulid.ulid(),
                'product_type': 'user_subscription',
                'product_id': 'prod_M0YTQKmiv45Zwi'
            },
            {
                'id': ulid.ulid(),
                'product_type': 'approver_subscription',
                'product_id': 'prod_MVCYn6qJFqRLbc'
            }
        ],
        'plans': [
            {
                'id': ulid.ulid(),
                'product_type': 'user_subscription',
                'stripe_plan_id': 'price_1LIXMUE0SvQaZIgKDmalhm4U',
                'plan_key': 'Free',
                'plan_description': 'All the basics for accounts payable automation. No credit card required.',
                'included_features': 'Add 5 Invoices Every Month;',
                'plan_price': 'Free',
                'max_approvers': None,
                'max_approvers_raw': None
            },
            {
                'id': ulid.ulid(),
                'product_type': 'user_subscription',
                'stripe_plan_id': 'price_1LhBRtE0SvQaZIgKQ0NMO9nn',
                'plan_key': 'Premium',
                'plan_description': 'Everything needed to manage your organization\'s invoices.',
                'included_features': 'Unlimited Invoices;',
                'plan_price': '29',
                'max_approvers': None,
                'max_approvers_raw': None
            },
            {
                'id': ulid.ulid(),
                'product_type': 'approver_subscription',
                'stripe_plan_id': 'price_1LmGPwE0SvQaZIgKHB2JjJho',
                'plan_key': 'One Approver',
                'plan_description': None,
                'included_features': None,
                'plan_price': '15',
                'max_approvers': 1,
                'max_approvers_raw': 'One'
            },
            {
                'id': ulid.ulid(),
                'product_type': 'approver_subscription',
                'stripe_plan_id': 'price_1LmC9XE0SvQaZIgKyQ3NImTY',
                'plan_key': 'Two Approver',
                'plan_description': None,
                'included_features': None,
                'plan_price': '30',
                'max_approvers': 2,
                'max_approvers_raw': 'Two'
            }
        ]
    }
else:
    # producion data
    INITIAL_DATA = {
        'products': [
            {
                'id': ulid.ulid(),
                'product_type': 'user_subscription',
                'product_id': 'prod_MBQP2bKoHpppFU'
            },
            {
                'id': ulid.ulid(),
                'product_type': 'approver_subscription',
                'product_id': 'prod_MiPHn7uMmKz6TA'
            }
        ],
        'plans': [
            {
                'id': ulid.ulid(),
                'product_type': 'user_subscription',
                'stripe_plan_id': 'price_1LT3YjE0SvQaZIgKHpxYsv07',
                'plan_key': 'Free',
                'plan_description': 'All the basics for accounts payable automation. No credit card required.',
                'included_features': 'Add 5 Invoices Every Month;',
                'plan_price': 'Free',
                'max_approvers': None,
                'max_approvers_raw': None
            },
            {
                'id': ulid.ulid(),
                'product_type': 'user_subscription',
                'stripe_plan_id': 'price_1LT3YjE0SvQaZIgKcUtZt8wJ',
                'plan_key': 'Premium',
                'plan_description': 'Everything needed to manage your organization\'s invoices.',
                'included_features': 'Unlimited Invoices;',
                'plan_price': '29',
                'max_approvers': None,
                'max_approvers_raw': None
            },
            {
                'id': ulid.ulid(),
                'product_type': 'approver_subscription',
                'stripe_plan_id': 'price_1LyyTLE0SvQaZIgKefAbZqfY',
                'plan_key': 'One Approver',
                'plan_description': None,
                'included_features': None,
                'plan_price': '15',
                'max_approvers': 1,
                'max_approvers_raw': 'One'
            },
            {
                'id': ulid.ulid(),
                'product_type': 'approver_subscription',
                'stripe_plan_id': 'price_1LyyTLE0SvQaZIgKTusJhKfp',
                'plan_key': 'Two Approver',
                'plan_description': None,
                'included_features': None,
                'plan_price': '30',
                'max_approvers': 2,
                'max_approvers_raw': 'Two'
            }
        ]
    }

def initialize_table():
    products_table = table('products',
        column('id', sa.String()),
        column('product_type', sa.String()),
        column('product_id', sa.String())
    )
    op.bulk_insert(products_table, INITIAL_DATA['products'])

    plans_table = table('plans',
        column('id', sa.String()),
        column('product_type', sa.String()),
        column('stripe_plan_id', sa.String()),
        column('plan_key', sa.String()),
        column('plan_description', sa.String()),
        column('included_features', sa.String()),
        column('plan_price', sa.String()),
        column('max_approvers', sa.Integer()),
        column('max_approvers_raw', sa.String())
    )
    op.bulk_insert(plans_table, INITIAL_DATA['plans'])


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('plans',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('product_type', sa.String(), nullable=False),
    sa.Column('stripe_plan_id', sa.String(), nullable=False),
    sa.Column('plan_key', sa.String(), nullable=False),
    sa.Column('plan_description', sa.String(), nullable=True),
    sa.Column('included_features', sa.String(), nullable=True),
    sa.Column('max_approvers', sa.Integer(), nullable=True),
    sa.Column('max_approvers_raw', sa.String(), nullable=True),
    sa.Column('plan_price', sa.String(), nullable=False),
    sa.Column('created_on', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('products',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('product_type', sa.String(), nullable=False),
    sa.Column('product_id', sa.String(), nullable=False),
    sa.Column('created_on', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('product_type')
    )
    initialize_table()
    op.create_table('approver_tier_settings',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('approval_tier', sa.String(), nullable=False),
    sa.Column('user_id', sa.String(), nullable=False),
    sa.Column('amount_from', sa.Integer(), nullable=True),
    sa.Column('amount_to', sa.Integer(), nullable=True),
    sa.Column('category', sa.String(), nullable=False),
    sa.Column('role', sa.String(), nullable=False),
    sa.Column('created_on', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('invited_approvers',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('first_name', sa.String(), nullable=True),
    sa.Column('last_name', sa.String(), nullable=True),
    sa.Column('email', sa.String(), nullable=False),
    sa.Column('invited_by', sa.String(), nullable=False),
    sa.Column('approval_tier', sa.String(), nullable=True),
    sa.Column('invited_on', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
    sa.ForeignKeyConstraint(['invited_by'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('subscriptions',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('user_id', sa.String(), nullable=False),
    sa.Column('plan_id', sa.String(), nullable=False),
    sa.Column('subscription_id', sa.String(), nullable=False),
    sa.Column('product_type', sa.String(), nullable=False),
    sa.Column('subscribed_at', sa.DateTime(), nullable=True),
    sa.Column('expires_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['plan_id'], ['plans.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('requested_approvers',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('invited_by', sa.String(), nullable=False),
    sa.Column('invited_approver', sa.String(), nullable=False),
    sa.Column('created_on', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
    sa.Column('valid_till', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['invited_approver'], ['invited_approvers.id'], ),
    sa.ForeignKeyConstraint(['invited_by'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('requested_approvers')
    op.drop_table('subscriptions')
    op.drop_table('invited_approvers')
    op.drop_table('approver_tier_settings')
    op.drop_table('products')
    op.drop_table('plans')
    # ### end Alembic commands ###
