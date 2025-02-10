from secrets import token_urlsafe

import ulid
from sqlalchemy import ARRAY, DECIMAL, Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.session import Base


def generate_token():
    return token_urlsafe(128)


class User(Base):
    __tablename__ = "users"

    id = Column(String, default=ulid.ulid, primary_key=True)
    organization_id = Column(String, ForeignKey("organizations.id"))
    invoices = relationship("Invoice")
    organization = relationship("Organization", viewonly=True)

    name = Column(String, nullable=True)
    role = Column(String, nullable=True)
    paid_plan = Column(String, nullable=True)
    upload_invoice_count = Column(Integer, default=0, nullable=True)
    last_invoice_upload_month = Column(Integer, nullable=True)
    stripe_session_id = Column(String, nullable=True)
    email = Column(String, nullable=False, unique=True)
    password_hash = Column(String, nullable=False)
    customer_id = Column(String, nullable=True, default=None)

    plan_started = Column(
        DateTime,
    )
    plan_expiry = Column(
        DateTime,
    )
    plan_id = Column(String)

    created_on = Column(DateTime, server_default=func.now())
    updated_on = Column(DateTime, onupdate=func.now())


class ResetPasswordToken(Base):
    __tablename__ = "reset_password_tokens"

    id = Column(String, default=ulid.ulid, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    token = Column(String, default=generate_token, nullable=False)
    created_on = Column(DateTime, server_default=func.now())


class Organization(Base):
    __tablename__ = "organizations"

    id = Column(String, default=ulid.ulid, primary_key=True)
    users = relationship("User")
    leads = relationship("Lead")
    invoices = relationship("Invoice")

    name = Column(String)
    address = Column(String)
    legal_business_type = Column(String)

    created_on = Column(DateTime, server_default=func.now())
    updated_on = Column(DateTime, onupdate=func.now())


class Vendor(Base):
    __tablename__ = "vendors"

    id = Column(String, default=ulid.ulid, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=True, index=True)
    organization_id = Column(
        String, ForeignKey("organizations.id"), nullable=True, index=True
    )
    invoices = relationship("Invoice")

    name = Column(String)
    aliases = Column(ARRAY(String), default=[])
    contact_email = Column(String)
    vendor_number = Column(Integer, unique=True)
    external_vendor_id = Column(Integer, unique=True)
    address_one = Column(String, default='')
    address_two = Column(String, default='')
    city = Column(String, default='')
    state = Column(String, default='')
    pincode = Column(Integer)
    attention = Column(String, default='')
    phone = Column(String, unique=True, default='')
    fax = Column(String, default='')
    parent_vendor = Column(Integer, unique=True)
    account = Column(String, default='')
    tax_id = Column(String, default='')
    note = Column(String, default='')
    
    created_on = Column(DateTime, server_default=func.now())
    updated_on = Column(DateTime, onupdate=func.now())


class InvoiceAttachment(Base):
    __tablename__ = "invoice_attachments"

    id = Column(String, default=ulid.ulid, primary_key=True)
    invoice_id = Column(
        String, ForeignKey("invoices.id"), nullable=False
    )
    attachment = Column(String, nullable=False)
    attachment_type = Column(String, nullable=False)
    created_on = Column(DateTime, server_default=func.now())


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(String, default=ulid.ulid, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=True, index=True)
    organization_id = Column(
        String, ForeignKey("organizations.id"), nullable=True, index=True
    )
    vendor_id = Column(String, ForeignKey("vendors.id"), nullable=True, index=True)
    content_hash = Column(String)

    is_paid = Column(Boolean, default=False)
    is_rejected = Column(Boolean, default=False)
    is_approved = Column(Boolean, default=False)
    rejection_reason = Column(String, nullable=True)
    vendor_name = Column(String)
    amount_due = Column(DECIMAL)
    currency = Column(String)
    due_date = Column(DateTime)
    invoice_id = Column(String)
    image_path = Column(String)
    image_content_type = Column(String)

    attachment = Column(String, nullable=True)

    raw_vendor_name = Column(String)
    raw_amount_due = Column(String)
    raw_due_date = Column(String)

    category_links = relationship(
        "CategoryInvoiceAssociation", back_populates="invoice"
    )

    created_on = Column(DateTime, server_default=func.now())
    updated_on = Column(DateTime, onupdate=func.now())


class Category(Base):
    __tablename__ = "categories"

    id = Column(String, default=ulid.ulid, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=True, index=True)
    organization_id = Column(
        String, ForeignKey("organizations.id"), nullable=True, index=True
    )

    name = Column(String)

    invoice_links = relationship(
        "CategoryInvoiceAssociation", back_populates="category"
    )

    created_on = Column(DateTime, server_default=func.now())
    updated_on = Column(DateTime, onupdate=func.now())


class CategoryInvoiceAssociation(Base):
    __tablename__ = "category_invoice_associations"

    category_id = Column(ForeignKey("categories.id"), primary_key=True)
    invoice_id = Column(ForeignKey("invoices.id"), primary_key=True)

    category = relationship("Category", back_populates="invoice_links")
    invoice = relationship("Invoice", back_populates="category_links")

    created_on = Column(DateTime, server_default=func.now())
    updated_on = Column(DateTime, onupdate=func.now())


class AgingReport(Base):
    __tablename__ = "ageing_reports"

    id = Column(String, default=ulid.ulid, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=True, index=True)
    organization_id = Column(
        String, ForeignKey("organizations.id"), nullable=True, index=True
    )

    csv_uri = Column(String)

    created_on = Column(DateTime, server_default=func.now())
    updated_on = Column(DateTime, onupdate=func.now())


class PaymentDetails(Base):
    __tablename__ = "payment_details"
    id = Column(String, default=ulid.ulid, primary_key=True)
    user_id = Column(String)
    type = Column(String)
    invoice_number = Column(String)
    account = Column(String)
    amount = Column(DECIMAL)
    account_number = Column(String)
    vendor = Column(String)
    date = Column(DateTime, server_default=func.now())


class Product(Base):
    __tablename__ = "products"
    id = Column(String, default=ulid.ulid, primary_key=True)
    product_type = Column(String, nullable=False, unique=True)
    product_id = Column(String, nullable=False)
    created_on = Column(DateTime, server_default=func.now())


class Plan(Base):
    __tablename__ = "plans"
    id = Column(String, default=ulid.ulid, primary_key=True)
    product_type = Column(String, nullable=False)
    stripe_plan_id = Column(String, nullable=False)
    plan_key = Column(String, nullable=False)
    plan_description = Column(String, nullable=True)
    included_features = Column(String, nullable=True)
    max_approvers = Column(Integer, nullable=True)
    max_approvers_raw = Column(String, nullable=True)
    plan_price = Column(String, nullable=False)
    created_on = Column(DateTime, server_default=func.now())

    @property
    def features(self):
        return [x for x in self.included_features.split(';')]

    @property
    def raw_amount(self):
        try:
            int(self.plan_price)
        except ValueError:
            return self.plan_price
        return f'${self.plan_price}'


class Subscription(Base):
    __tablename__ = "subscriptions"
    id = Column(String, default=ulid.ulid, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    plan_id = Column(String, ForeignKey("plans.id"), nullable=False)
    subscription_id = Column(String, nullable=False)
    product_type = Column(String, nullable=False)
    subscribed_at = Column(DateTime)
    expires_at = Column(DateTime)


class ApproverTierSetting(Base):
    __tablename__ = "approver_tier_settings"
    id = Column(String, default=ulid.ulid, primary_key=True)
    approval_tier = Column(String, nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    amount_from = Column(Integer, nullable=True)
    amount_to = Column(Integer, nullable=True)
    category = Column(String, nullable=False)
    role = Column(String, nullable=True)
    created_on = Column(DateTime, server_default=func.now())


class InvitedApprover(Base):
    __tablename__ = "invited_approvers"
    id = Column(String, default=ulid.ulid, primary_key=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    email = Column(String, nullable=False)
    invited_by = Column(String, ForeignKey("users.id"), nullable=False)
    approval_tier = Column(String, nullable=True)
    invited_on = Column(DateTime, server_default=func.now())

class RequestedApprover(Base):
    __tablename__ = "requested_approvers"

    id = Column(String, default=ulid.ulid, primary_key=True)
    invited_by = Column(String, ForeignKey("users.id"), nullable=False)
    invited_approver = Column(String, ForeignKey("invited_approvers.id"), nullable=False)
    invoice_id = Column(String, nullable=True)
    created_on = Column(DateTime, server_default=func.now())
    valid_till = Column(DateTime)


class Lead(Base):
    __tablename__ = "leads"

    id = Column(String, default=ulid.ulid, primary_key=True)
    create_date = Column(DateTime, server_default=func.now())
    company = Column(String, ForeignKey("organizations.id"))
    organization = relationship("Organization", viewonly=True)
    name = Column(String, nullable=True)
    email = Column(String, nullable=False)
    meta = Column(String, nullable=True)
    source = Column(String, nullable=True)
    reference = Column(String, nullable=True)
    edit = Column(String, nullable=True)
