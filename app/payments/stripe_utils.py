from datetime import date
from typing import Optional

import sqlalchemy as sa
import stripe

import app.db.models as db_models
from app.users.db_utils import get_user_by_id

from .config import config

stripe.api_key = config.stripe_secret_key


def stripeUser(name, email):
    response = stripe.Customer.create(name=name, email=email)
    return response.get("id") if response.get("id") else ""


def update_user_plan(
    db: sa.orm.Session,
    user_id: str,
    paid_plan: str,
    plan_expiry: date,
    plan_started: date,
    plan_id: str,
) -> Optional[db_models.User]:
    user = get_user_by_id(db, user_id)
    if not user:
        return None

    user.paid_plan = paid_plan
    user.plan_expiry = plan_expiry
    user.plan_started = plan_started
    user.plan_id = plan_id
    db.commit()
    db.refresh(user)
    return user


def update_customer_id(
    db: sa.orm.Session, user_id: str, customer_id: str
) -> Optional[db_models.User]:
    user = get_user_by_id(db, user_id)
    if not user:
        return None

    user.customer_id = customer_id
    db.commit()
    db.refresh(user)
    return user
