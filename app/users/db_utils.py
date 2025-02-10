from typing import Optional

import sqlalchemy as sa

import app.db.models as db_models


def get_user_by_id(db: sa.orm.Session, user_id: str) -> Optional[db_models.User]:
    return db.query(db_models.User).filter_by(id=user_id).first()

def get_user_by_org_id(db: sa.orm.Session, organization_id: str) -> Optional[db_models.User]:
    return db.query(db_models.User).filter_by(organization_id=organization_id).first()

def get_user_by_email(db: sa.orm.Session, email: str) -> Optional[db_models.User]:
    return db.query(db_models.User).filter_by(email=email).first()