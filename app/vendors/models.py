from typing import List, Optional

import sqlalchemy as sa
from pydantic import BaseModel

from app.db.models import Vendor
from app.utils import format_date_american

from .db_utils import (
    get_invoice_last_added_on_by_vendor,
    get_total_due_by_vendor,
    get_total_invoice_count_by_vendor,
    get_total_paid_by_vendor,
)


class PublicVendorView(BaseModel):
    id: str
    name: str
    aliases: List[str] = []
    contact_email: str = None

    total_paid: str
    total_due: str
    currency: Optional[str] = "$"
    total_invoice_count: str

    last_added_on: Optional[str] = None
    created_on: str
    updated_on: str = None

    vendor_number: Optional[int] = None
    external_vendor_id: Optional[int]  = None
    address_one: Optional[str] = None
    address_two: Optional[str] = None
    city: Optional[str]= None
    state: Optional[str] = None
    pincode: Optional[int] = None
    attention: Optional [str] = None
    phone: Optional[str] = None
    fax: Optional[str] = None
    parent_vendor: Optional[int] = None
    account: Optional[str] = None
    tax_id: Optional[str] = None
    note: Optional[str] = None
    
    @classmethod
    def load(cls, db: sa.orm.Session, vendor: Vendor) -> "PublicVendorView":
        total_due = get_total_due_by_vendor(db, vendor.id)
        total_paid = get_total_paid_by_vendor(db, vendor.id)
        total_invoice_count = get_total_invoice_count_by_vendor(db, vendor.id)
        last_added_on = get_invoice_last_added_on_by_vendor(db, vendor.id)

        # TODO: Allow for multiple currencies
        return cls(
            currency="$",
            total_due=total_due,
            total_paid=total_paid,
            total_invoice_count=total_invoice_count,
            last_added_on=format_date_american(last_added_on),
            id=vendor.id,
            name=vendor.name,
            aliases=vendor.aliases,
            contact_email=vendor.contact_email,
            created_on=format_date_american(vendor.created_on),
            updated_on=format_date_american(vendor.updated_on),
            vendor_number=vendor.vendor_number if vendor.vendor_number is not None else 0,
            external_vendor_id=vendor.external_vendor_id if vendor.external_vendor_id is not None else 0,
            address_one=vendor.address_one if vendor.address_one is not None else '',
            address_two=vendor.address_two if vendor.address_two is not None else '',
            city=vendor.city if vendor.city is not None else '',
            state=vendor.state if vendor.state is not None else '',
            pincode=vendor.pincode if vendor.pincode is not None else 0,
            attention=vendor.attention if vendor.attention is not None else '',
            phone=vendor.phone if vendor.phone is not None else '',
            fax=vendor.fax if vendor.fax is not None else '',
            parent_vendor=vendor.parent_vendor if vendor.parent_vendor is not None else 0,
            account=vendor.account if vendor.account is not None else '',
            tax_id=vendor.tax_id if vendor.tax_id is not None else '',
            note=vendor.note if vendor.note is not None else ''
        )
