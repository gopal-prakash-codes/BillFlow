import json
from typing import Optional

from fastapi import Request
from pydantic import BaseModel

import app.db.models as db_models
from app.auth.models import UserRoleEnum


class UserSession(BaseModel):
    user_id: Optional[str] = None
    role: Optional[UserRoleEnum] = UserRoleEnum.default
    organization_id: Optional[str] = None
    customer_id: Optional[str] = None
    email: Optional[str] = None
    name: Optional[str] = None

    @classmethod
    def from_user(cls, user: db_models.User) -> "UserSession":
        return UserSession(
            user_id=user.id,
            role=user.role,
            organization_id=user.organization_id,
            customer_id=user.customer_id,
            email=user.email,
            name=user.name,
        )


def set_session(req: Request, data: UserSession) -> None:
    """Modifies Request.session in place"""
    jsonable_dict: dict = json.loads(data.json())
    for k, v in jsonable_dict.items():
        req.session[k] = v


def clear_session(req: Request) -> None:
    """Modifies Request.session in place"""
    set_session(req, UserSession())
