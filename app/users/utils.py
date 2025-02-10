from app.db.session import SessionLocal

import app.db.models as db_models

import sqlalchemy as sa


def get_approvers_list(user_id: int):
    with SessionLocal() as db:
        return db.query(db_models.InvitedApprover).filter_by(invited_by=user_id)


def add_visitor(
    db: sa.orm.Session, email: str
):
    new_lead = db_models.Lead(
        email=email,
        meta="Newsletter",
        reference="Web Visitor"
    )
    db.add(new_lead)
    db.commit()
    db.refresh(new_lead)
    return new_lead
