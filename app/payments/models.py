from fastapi import Form

from enum import Enum

from pydantic import BaseModel


class PaymentPlanEnum(str, Enum):
    free = "free"
    premium = "premium"
    corporate = "corporate"


class TierEnum(str, Enum):
    tier_1 = "Tier 1"
    tier_2 = "Tier 2"
    tier_3 = "tier 3"


class ProductTypeEnum(str, Enum):
    user_subscription = "user_subscription"
    approver_subscription = "approver_subscription"

class RequestPlan(BaseModel):
    price_id: str
    payment_method: str

    class Config:
        orm_mode = True


class PriceID(BaseModel):
    price_id: str

    class config:
        orm_mode = True


class PaymentDetailsType(str, Enum):
    check = "check"
    card = "card"
