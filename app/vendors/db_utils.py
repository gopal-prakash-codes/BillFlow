from datetime import datetime
from typing import List, Optional

import sqlalchemy as sa
from sqlalchemy.sql import desc, func

import app.db.models as db_models


def get_vendors_by_user(db: sa.orm.Session, user_id: int) -> List[db_models.Vendor]:
    return db.query(db_models.Vendor).filter_by(user_id=user_id).all()


def get_vendor_by_id(db: sa.orm.Session, id: str) -> Optional[db_models.Vendor]:
    return db.query(db_models.Vendor).filter_by(id=id).first()


def get_total_paid_by_vendor(db: sa.orm.Session, vendor_id: str) -> int:
    return (
        db.query(func.sum(db_models.Invoice.amount_due))
        .filter_by(vendor_id=vendor_id, is_paid=True)
        .scalar()
        or 0
    )


def get_total_due_by_vendor(db: sa.orm.Session, vendor_id: str) -> int:
    return (
        db.query(func.sum(db_models.Invoice.amount_due))
        .filter_by(vendor_id=vendor_id, is_paid=False)
        .scalar()
        or 0
    )


def get_total_invoice_count_by_vendor(db: sa.orm.Session, vendor_id: str) -> int:
    return (
        db.query(func.count(db_models.Invoice.id))
        .filter_by(vendor_id=vendor_id)
        .scalar()
        or 0
    )


def get_invoice_last_added_on_by_vendor(
    db: sa.orm.Session, vendor_id: str
) -> Optional[datetime]:
    res = (
        db.query(db_models.Invoice)
        .filter_by(vendor_id=vendor_id)
        .order_by(desc(db_models.Invoice.created_on))
        .first()
    )
    if not res:
        return None
    return res.created_on


def update_vendor_contact_email(
    db: sa.orm.Session, vendor_id: str, email: str
) -> Optional[db_models.Vendor]:
    vendor = get_vendor_by_id(db, vendor_id)
    if not vendor:
        return None

    vendor.contact_email = email
    db.commit()
    db.refresh(vendor)
    return vendor
from sqlalchemy.exc import IntegrityError

def update_vendor_info(
    db: sa.orm.Session, vendor_id: str, body: dict
) -> Optional[db_models.Vendor]:
    vendor = get_vendor_by_id(db, vendor_id)
    if not vendor:
        return (None, "Vendor not found")

    try:
        if body['vendor_number'] != 0:
            vendor.vendor_number=body['vendor_number']
        if body['external_vendor_id'] != 0:
            vendor.external_vendor_id=body['external_vendor_id']
        if body['pincode'] != 0:
            vendor.pincode=body['pincode']
        if body['parent_vendor'] != 0:
            vendor.parent_vendor=body['parent_vendor']
        if  body['phone'] != '':
            vendor.phone=body['phone']

        vendor.address_one=body['address_one'],
        vendor.address_two=body['address_two'],
        vendor.city=body['city'],
        vendor.state=body['state'],
        vendor.attention=body['attention'],
        vendor.fax=body['fax'],
        vendor.account=body['account'],
        vendor.tax_id=body['tax_id'],
        vendor.note=body['note']

        db.commit()
        db.refresh(vendor)
        return (True, vendor)
    except IntegrityError as e:
        db.rollback()
        return (None, e.args[0].split('key')[-1])


def add_leads_data(
    db: sa.orm.Session, email: str, organization_id: str
):
    company = db.query(db_models.Organization).filter_by(id=organization_id).first()
    new_lead = db_models.Lead(
        email=email,
        company=organization_id,
        meta=company.name,
        reference='Vendor'
    )
    db.add(new_lead)
    db.commit()
    db.refresh(new_lead)
    return new_lead


def update_leads_by_organization_id(
    db: sa.orm.Session, email: str, organization_id: str   
):
    # Note: This can be used if needed to update the Accountant email.
    # lead = db.query(db_models.Lead).filter_by(meta=organization_id)
    # if lead.first():
    #     lead.update({db_models.Lead.reference: email})
    #     db.commit()
    # else:

    # Add Accountant to leads table
    company = db.query(db_models.Organization).filter_by(id=organization_id).first()
    new_lead = db_models.Lead(
        email=email,
        company=organization_id,
        meta=company.name,
        reference='Accountant'
    )
    db.add(new_lead)
    db.commit()
    db.refresh(new_lead)
    return new_lead
