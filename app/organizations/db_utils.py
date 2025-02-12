from typing import Optional

from sqlalchemy.orm import Session

from app.db.models import Organization


def get_organization_by_id(db: Session, organization_id: str) -> Optional[Organization]:
    return db.query(Organization).filter_by(id=organization_id).one_or_none()
