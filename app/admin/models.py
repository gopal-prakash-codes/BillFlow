from typing import Optional

from pydantic import BaseModel

from app.db.models import User, Lead
from app.payments.models import PaymentPlanEnum
from app.utils import format_date_american


class AdminUserView(BaseModel):
    id: str
    company_name: Optional[str] = None
    email: str
    paid_plan: Optional[str] = PaymentPlanEnum.free
    created_on: str
    last_payment_made: Optional[str] = None

    @classmethod
    def load_from_db(cls, user: User) -> "AdminUserView":
        return AdminUserView(
            id=user.id,
            company_name=user.organization.name if user.organization else None,
            email=user.email,
            paid_plan=user.paid_plan,
            created_on=format_date_american(user.created_on),
            last_payment_made=None,
        )


class AdminLeadsView(BaseModel):
    id: str
    company: Optional[str] = None
    email: str
    name: Optional[str] = None
    organization: Optional[str] = None
    create_date: str
    meta: Optional[str] = None
    reference: Optional[str] = None

    @classmethod
    def load_from_db(cls, lead: Lead) -> "AdminLeadsView":
        return AdminLeadsView(
            id=lead.id,
            company=lead.organization.name if lead.organization else None,
            email=lead.email,
            meta=lead.meta,
            reference=lead.reference,
            create_date=format_date_american(lead.create_date),
        )
