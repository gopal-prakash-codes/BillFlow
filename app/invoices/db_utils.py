from datetime import datetime
from decimal import Decimal
from typing import List, Optional

import sqlalchemy as sa
from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import func

from app.db.models import (
    AgingReport,
    Category,
    CategoryInvoiceAssociation,
    InvitedApprover,
    Invoice,
    InvoiceAttachment,
    PaymentDetails,
    Vendor,
    RequestedApprover,
    Subscription
)
from app.payments.models import ProductTypeEnum
from app.users.db_utils import get_user_by_id

from .models import CreateInvoice, PaginateInvoice


def get_invoice_by_id(db: Session, invoice_id: str) -> Optional[Invoice]:
    return db.query(Invoice).filter_by(id=invoice_id).first()

def get_invited_approvers(db: Session, user_id: str) -> List:
    return db.query(InvitedApprover).filter_by(invited_by=user_id).all()


def ensure_vendor_by_name(db: sa.orm.Session, vendor_name: str, user_id: str) -> Vendor:
    # TODO: proper upsert? And need to set organization id.
    existing = db.query(Vendor).filter_by(name=vendor_name, user_id=user_id).first()
    if existing:
        return existing

    new = Vendor(
        name=vendor_name,
        user_id=user_id,
    )

    db.add(new)
    db.commit()
    db.refresh(new)
    return new


def save_invoice(db: Session, invoice: CreateInvoice) -> Invoice:
    """Saves invoice - ensures vendor exists and sets orgnaization id that corresponds to user creating the invoice"""
    db_invoice = invoice.to_orm()
    db_vendor = ensure_vendor_by_name(db, db_invoice.vendor_name, invoice.user_id)
    db_invoice.vendor_id = db_vendor.id

    user = get_user_by_id(db, invoice.user_id)
    db_invoice.organization_id = user.organization_id

    db.add(db_invoice)
    db.commit()
    db.refresh(db_invoice)
    return db_invoice


def query_invoices(
    db: Session,
    *,
    user_id: str = None,
    organization_id: str = None,
    vendor_id: str = None,
    filter_by: str = None,
    order_by: str = "due_date",
    limit: int = 5,
    offset: int = 0,
    desc: bool = False,
    due_date: datetime = None,
    due_after: datetime = None,
    due_before: datetime = None,
    invoice_number: str = None,
    total_pages: int = 0,
    current_page: int = 1
) -> PaginateInvoice:
    """Retrieves invoices from db

    Args:
        db (Session): SessionLocal object
        user_id (str): User to pull invoices from.
        vendor_id (str): Vendor to pull invoice from
        order_by (str, optional): Name of column to order by. Defaults to "due_date".
        desc (bool, optional): Indicates if results should be sorted in a desc fashion or not (i.e. asc).
        Defaults to False.
        limit (int, optional): Max number of results to be returned. Defaults to 100.
        offset (int, optional): Offset to allow for pagination. Defaults to 0.

    NOTE: Either one of or both of vendor_id and user_id must be provided

    Returns:
        List[Invoice]
    """
    if not user_id and not vendor_id and not organization_id:
        raise Exception("At least on of user_id and vendor_id must be provided")

    invoices_query = db.query(Invoice)

    if user_id:
        invoices_query = invoices_query.filter_by(user_id=user_id)
    if organization_id:
        invoices_query = invoices_query.filter_by(organization_id=organization_id)
    if vendor_id:
        invoices_query = invoices_query.filter_by(vendor_id=vendor_id)

    if filter_by:
        if filter_by == "paid":
            invoices_query = invoices_query.filter_by(is_paid=True)
        elif filter_by == "due":
            invoices_query = invoices_query.filter_by(is_paid=False)
        elif filter_by == "approved":
            invoices_query = invoices_query.filter_by(is_approved=True)
        elif filter_by == "all":
            # TODO Add enumerations
            pass

    if due_date:
        invoices_query = invoices_query.filter(Invoice.due_date == due_date)
    
    if invoice_number:
        invoices_query = invoices_query.filter_by(invoice_id=invoice_number)

    # if due_after:
    #     invoices_query = invoices_query.filter(Invoice.is_paid == False)

    if due_before:
        invoices_query = invoices_query.filter(Invoice.due_date <= due_before)

    try:
        order_by_stmt = getattr(Invoice, order_by)
    except AttributeError:
        return []

    if desc:
        order_by_stmt = sa.desc(order_by_stmt)

    invoices_query = invoices_query.order_by(order_by_stmt)
    if total_pages == 1:
        all_invoices = invoices_query.all()
        total_pages = (len(all_invoices)/limit)
    invoices_query = invoices_query.limit(limit).offset(offset)
    invoices = invoices_query.all()
    return PaginateInvoice(
        items=invoices,
        limit=limit,
        offset=offset+limit,
        total_pages=total_pages,
        current_page=current_page
    )


def get_invoices_by_user(
    db: Session,
    user_id: str,
    filter_by: str = None,
    order_by: str = "due_date",
    limit: int = 100,
    offset: int = 0,
    total_pages: int = 1,
    current_page: int = 1,
    desc: bool = False,
    due_after: datetime = None,
) -> PaginateInvoice:
    return query_invoices(
        db,
        user_id=user_id,
        filter_by=filter_by,
        order_by=order_by,
        limit=limit,
        offset=offset,
        desc=desc,
        due_after=due_after,
        total_pages=total_pages,
        current_page=current_page
    )


def get_invoices_by_organization(
    db: Session,
    organization_id: str,
    vendor: str = None,
    due_date: str = None,
    invoice_number: str = None,
    total_pages: int = 1,
    current_page: int = 1
) -> PaginateInvoice:
    return query_invoices(
        db,
        organization_id=organization_id,
        vendor_id=vendor,
        due_date=due_date,
        invoice_number=invoice_number,
        total_pages=total_pages,
        current_page=current_page
    )


def update_paid_status_invoice(db: Session, invoice_id: str, is_paid: bool) -> Invoice:
    invoice = get_invoice_by_id(db, invoice_id)
    if not invoice:
        raise ValueError("Could not find Invoice with provided Invoice.id")
    invoice.is_paid = is_paid
    db.commit()
    return invoice


def add_attachment_obj_to_db(db: Session, invoice_id: str, object_name: str, attachment_type: str) -> Invoice:
    invoice = get_invoice_by_id(db, invoice_id)
    if not invoice:
        raise ValueError("Could not find Invoice with provided Invoice.id")
    invoice_attachment = InvoiceAttachment(
        invoice_id=invoice.id,
        attachment=object_name,
        attachment_type=attachment_type
    )
    db.add(invoice_attachment)
    db.commit()
    db.refresh(invoice_attachment)
    return invoice_attachment


def can_upload_attachment(db: Session, user_id: str) -> tuple:
    user = get_user_by_id(db, user_id)
    user_approver_subscription = db.query(Subscription).filter_by(user_id=user_id, product_type=ProductTypeEnum.approver_subscription).first()
    return user_approver_subscription, user.last_invoice_upload_month


def can_upload(db: Session, user_id: str) -> tuple:
    user = get_user_by_id(db, user_id)
    return user.paid_plan, user.last_invoice_upload_month


def invoice_upload_count(db: Session, user_id: str) -> int:
    user = get_user_by_id(db, user_id)
    return user.upload_invoice_count

def update_invoice_upload_count(db: Session, user_id: str, current_month: Optional[int] = None) -> bool:
    user = get_user_by_id(db, user_id)

    if current_month:
        user.last_invoice_upload_month = datetime.now().month
        user.upload_invoice_count = 0
        db.commit()
        return True
    
    user.upload_invoice_count += 1
    db.commit()
    return True


def get_num_due_soon(db: sa.orm.Session, user_id: str) -> int:
    return (
        db.query(func.count(Invoice.id))
        .filter_by(user_id=user_id, is_paid=False)
        .filter(Invoice.due_date > datetime.utcnow())
        .scalar()
        or 0
    )


def get_num_overdue(db: sa.orm.Session, user_id: str) -> int:
    return (
        db.query(func.count(Invoice.id))
        .filter_by(user_id=user_id, is_paid=False)
        .filter(Invoice.due_date < datetime.utcnow())
        .scalar()
        or 0
    )


def get_num_paid(db: sa.orm.Session, user_id: str) -> int:
    return (
        db.query(func.count(Invoice.id))
        .filter_by(user_id=user_id, is_paid=True)
        .scalar()
        or 0
    )


def get_invoice_links_by_category_name(
    db: sa.orm.Session, name: str, user_id: str
) -> List[CategoryInvoiceAssociation]:
    category = db.query(Category).filter_by(name=name, user_id=user_id).first()
    if not category:
        return []
    return category.invoice_links


def get_category_by_name(
    db: sa.orm.Session, name: str, user_id: str
) -> Optional[Category]:
    return db.query(Category).filter_by(user_id=user_id, name=name).first()


# TODO: Gotta do these upserts right
# TODO: user_id should translate to organization id
def ensure_category_by_name(
    db: sa.orm.Session, name: str, user_id: str, commit: bool = True
) -> Category:
    name = name.strip()

    existing = db.query(Category).filter_by(name=name, user_id=user_id).first()
    if existing:
        return existing

    new = Category(
        name=name,
        user_id=user_id,
    )

    db.add(new)

    if commit:
        db.commit()
    else:
        db.flush()

    db.refresh(new)
    return new


def get_category_link_by_invoice_id_and_name(
    db: sa.orm.Session, user_id: str, invoice_id: str, category_name: str
) -> Optional[CategoryInvoiceAssociation]:
    return (
        db.query(CategoryInvoiceAssociation)
        .join(Category, CategoryInvoiceAssociation.category_id == Category.id)
        .filter(CategoryInvoiceAssociation.invoice_id == invoice_id)
        .filter(Category.name == category_name)
        .first()
    )


def add_category_to_invoice(
    db: sa.orm.Session, user_id: str, invoice_id: str, category_name: str
) -> CategoryInvoiceAssociation:
    existing_link = get_category_link_by_invoice_id_and_name(
        db, user_id, invoice_id, category_name
    )
    if existing_link:
        return existing_link

    # Remove existing links to ensure only one category
    db.query(CategoryInvoiceAssociation).filter_by(invoice_id=invoice_id).delete()

    category = ensure_category_by_name(db, category_name, user_id, commit=False)
    new_link = CategoryInvoiceAssociation(
        invoice_id=invoice_id, category_id=category.id
    )

    db.add(new_link)
    db.commit()
    db.refresh(new_link)
    return new_link


def remove_category_from_invoice(
    db: sa.orm.Session, user_id: str, invoice_id: str, category_name: str
) -> None:
    # TODO: remove from category table if no associations?
    existing_link = get_category_link_by_invoice_id_and_name(
        db, user_id, invoice_id, category_name
    )
    if not existing_link:
        return existing_link

    db.delete(existing_link)
    db.commit()


def delete_invoice(db: sa.orm.Session, invoice_id: str) -> None:
    # Delete category links
    db.query(CategoryInvoiceAssociation).filter_by(invoice_id=invoice_id).delete()
    # Delete invoice
    db.query(Invoice).filter_by(id=invoice_id).delete()
    db.commit()


def get_aging_report_by_id(db: Session, report_id: str) -> Optional[AgingReport]:
    return db.query(AgingReport).filter_by(id=report_id).first()


def query_aging_reports(
    db: Session,
    user_id: str,
    *,
    order_by: str,
    limit: int = 100,
    offset: int = 0,
    desc: bool = False,
) -> List[AgingReport]:

    query = db.query(AgingReport).filter_by(user_id=user_id)
    try:
        order_by_stmt = getattr(AgingReport, order_by)
    except AttributeError:
        return []

    if desc:
        order_by_stmt = sa.desc(order_by_stmt)

    query = query.order_by(order_by_stmt)
    query = query.limit(limit).offset(offset)
    return query.all()


def get_payment_details(
    db: Session,
    user_id: str,
    invoice_id: str
):
    invoice = db.query(Invoice).get(invoice_id)
    payment_detail = db.query(PaymentDetails).filter_by(invoice_number=invoice.invoice_id, user_id=user_id).first()
    return payment_detail


def get_invoice_due_amount(
    db: Session,
    invoice_id: str
):
    invoice = db.query(Invoice).get(invoice_id)
    return str(invoice.amount_due)


def get_invoice_details(
    db: Session,
    invoice_id: str
):
    invoice = db.query(Invoice).get(invoice_id)
    return invoice


def save_payment_details(
    payment_type: str,
    account: str,
    amount: Decimal,
    account_number: str,
    vendor: str,
    date: datetime,
    invoice_id: str,
    user_id: str = None,
    db: Session = None,
):
    invoice = db.query(Invoice).get(invoice_id)
    payment_detail = PaymentDetails(
        user_id=user_id,
        type=payment_type,
        account=account,
        amount=amount,
        account_number=account_number,
        date=date,
        vendor=vendor,
        invoice_number=invoice.invoice_id
    )
    db.add(payment_detail)
    db.commit()
    db.refresh(payment_detail)
    invoice.is_paid = True
    db.add(invoice)
    db.commit()
    db.refresh(invoice)
    return payment_detail


def cancel_invoice_request(db: sa.orm.Session, invoice_id: str) -> None:
    db.query(RequestedApprover).filter_by(invoice_id=invoice_id).delete()
    db.commit()
    invoice = get_invoice_by_id(db=db, invoice_id=invoice_id)
    invoice.is_rejected = False
    db.commit()


def has_attachments(db: Session, invoice_id: str) -> bool:
    attachments = db.query(InvoiceAttachment).filter(InvoiceAttachment.invoice_id == invoice_id).all()
    return bool(attachments)
