from secrets import token_urlsafe
from typing import Optional

from fastapi import Request
from fastapi.exceptions import HTTPException
from passlib.hash import bcrypt
from sqlalchemy.orm import Session
from starlette import status

import app.db.models as db_models
from app.auth.models import UserRoleEnum

from .session_utils import UserSession


def hash_pswd(pswd: str):
    return bcrypt.encrypt(pswd)


def verify_pswd(pswd: str, hashed: str) -> bool:
    return bcrypt.verify(pswd, hashed)


def redirect_authentication(req: Request) -> str:
    session = UserSession(**req.session)
    if not session.user_id:
        raise HTTPException(
            status_code=status.HTTP_302_FOUND, headers={"Location": "/landing"}
        )
    return session.user_id


def requires_authentication(req: Request) -> str:
    session = UserSession(**req.session)
    if not session.user_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Must be logged in.")
    return session.user_id


def admin_authentication(req: Request) -> str:
    session = UserSession(**req.session)
    if not session.user_id or session.role != UserRoleEnum.admin:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Unauthorizes")
    return session.user_id


def optional_authentication(req: Request) -> Optional[str]:
    # if not global_config.in_deployment:
    #     return 1
    # else:
    #     raise Exception("Forgot to update from testing env")

    session = UserSession(**req.session)
    if not session.user_id:
        return None
    return session.user_id


def create_reset_pwd_token(db: Session, user_id: str) -> db_models.ResetPasswordToken:
    token = db_models.ResetPasswordToken(user_id=user_id, token=token_urlsafe(128))
    db.add(token)
    db.commit()
    db.refresh(token)
    return token
