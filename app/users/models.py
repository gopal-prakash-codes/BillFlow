from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.auth.models import UserRoleEnum


class Organization(BaseModel):
    id: str
    name: str

    class Config:
        orm_mode = True


class Approver(BaseModel):
    id: str
    first_name: str
    last_name: str
    email: str
    approval_tier: Optional[str]

    class Config:
        orm_mode = True


class User(BaseModel):
    id: str
    organization: Organization
    name: str = None
    email: str
    password_hash: str
    paid_plan: str = None
    role: Optional[UserRoleEnum] = UserRoleEnum.default
    stripe_session_id: str = None
    customer_id: str = None
    created_on: datetime
    updated_on: datetime = None

    class Config:
        orm_mode = True


class Accountant(BaseModel):
    accountant_name: str
    accountant_email: str

    class Config:
        orm_mode = True
