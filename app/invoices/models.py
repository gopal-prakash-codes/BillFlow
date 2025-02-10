import io
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Any, List, Optional, Union

import humanize
import pandas as pd
from loguru import logger as log
from pydantic import BaseModel, validator

from app.db.models import AgingReport, Invoice
from app.invoices.ocr.models import RawInvoiceBody
from app.utils import format_date_american
from app.db.schema import PaginateResponse
from .config import config
from .s3_utils import s3_client

from currency_symbols import CurrencySymbols


class InvoiceStatusEnum(str, Enum):
    due = "due"
    overdue = "overdue"
    paid = "paid"
    unknown = "unknown"
    approved = "approved"
    waiting_for_approval = "waiting for approval"

    @classmethod
    def get_status(
        cls, is_paid: bool, due_date: datetime = None
    ) -> "InvoiceStatusEnum":
        if is_paid:
            return cls.paid

        if not due_date:
            return cls.unknown

        if datetime.utcnow() > due_date:
            return cls.overdue

        return cls.due


class CreateInvoice(BaseModel):
    user_id: str

    is_paid: bool = False
    vendor_name: str = None
    amount_due: Decimal = None
    currency: Optional[str] = "USD"
    due_date: datetime = None
    invoice_id: str = None
    image_path: str = None
    image_content_type: str = None

    raw_vendor_name: str = None
    raw_amount_due: str = None
    raw_due_date: str = None

    @classmethod
    def from_raw_parse(
        cls, user_id: str, raw: RawInvoiceBody, content_type: str
    ) -> "CreateInvoice":
        return cls(
            user_id=user_id,
            vendor_name=raw.formatted_vendor_name,
            amount_due=raw.formatted_total_due,
            currency=raw.formatted_currency,
            due_date=raw.formatted_due_date,
            invoice_id=raw.invoice_number,
            raw_vendor_name=raw.vendor_name,
            raw_amount_due=raw.total_due,
            raw_due_date=raw.due_date,
            image_content_type=content_type,
        )

    def to_orm(self) -> Invoice:
        return Invoice(**self.dict())


class PublicInvoice(BaseModel):
    id: str
    is_paid: bool = None
    vendor_id: str = None
    vendor_name: str = None
    amount_due: Union[str, Decimal] = None
    status: str = None
    currency: Optional[str] = "USD"
    currency_symbol: str = ""
    due_date: datetime = None
    invoice_id: str = None
    image_path: str = None
    image_content_type: str = None
    humanized_due_date: Union[str, datetime] = None
    american_due_date: Union[str, datetime] = None
    category: str = None
    is_rejected: bool = False
    is_approved: bool = False
    rejection_reason: str = None
    approver_name: str = None

    @validator("humanized_due_date")
    def humanize_datetime(cls, v: datetime) -> str:
        if not isinstance(v, datetime):
            log.debug(f"Tried to parse {v}, {type(v)} as a humanized date.")
            return "unknown"
        current_time = datetime.utcnow()
        delta: timedelta = current_time - v
        return humanize.naturaltime(delta)

    @validator("amount_due")
    def enforce_two_decimal_places(cls, v: Decimal) -> Optional[str]:
        if not v:
            return None
        return f"{Decimal(v):.2f}"

    @classmethod
    def from_orm(cls, db_invoice: Invoice, approval_status=None, approver_name=None) -> "PublicInvoice":
        try:
            category = (
                db_invoice.category_links[0].category.name
                if db_invoice.category_links
                else None
            )
            # Set invoice currency
            if db_invoice.currency is None or db_invoice.currency == '$':
                currency_symbol = '$'
            elif db_invoice.currency:
                currency_symbol = CurrencySymbols.get_symbol(db_invoice.currency)
            if approval_status == 1: # false
                status_enum = InvoiceStatusEnum.approved
            elif approval_status == 0: # true
                status_enum = InvoiceStatusEnum.waiting_for_approval
            else:
                status_enum = InvoiceStatusEnum.get_status(
                    db_invoice.is_paid, db_invoice.due_date
                )
            return cls(
                category=category,
                humanized_due_date=db_invoice.due_date,
                american_due_date=format_date_american(db_invoice.due_date),
                status=status_enum.value,
                approver_name=approver_name,
                currency_symbol=currency_symbol,
                **db_invoice.__dict__,
            )
        except Exception:
            pass


class PublicAgingReport(BaseModel):
    id: str
    csv_uri: str
    american_date: str
    created_on: datetime

    @classmethod
    def from_orm(cls, db_report: AgingReport) -> "PublicAgingReport":
        return cls(
            american_date=format_date_american(db_report.created_on),
            **db_report.__dict__,
        )

    @property
    def as_df(self) -> pd.DataFrame:
        import numpy as np

        f = io.BytesIO()
        s3_client.download_fileobj(config.s3_bucket_name, self.csv_uri, f)
        f.seek(0)
        df = pd.read_csv(f, header=2)
        df = df.fillna("")
        df.replace(np.nan, 0, inplace=True)
        return df

    def csv_html(self) -> str:
        return self.as_df.to_html(index=False)


class CategoryEnum(str, Enum):
    purchases = "purchases"
    maintenance_and_repair = "maintenance_and_repair"
    entertainment = "entertainment"
    travel = "travel"
    equipment = "equipment"
    internet = "internet"
    hosting = "hosting"
    furniture = "furniture"
    office_supplies = "office_supplies"
    vehicles = "vehicles"
    accommodation = "accommodation"
    continuing_education = "continuing_education"
    conferences_and_seminars = "conferences_and_seminars"
    professional_fees = "professional_fees"
    marketing_and_advertising = "marketing_and_advertising"
    business_insurance = "business_insurance"
    software_and_subscription_services = "software_and_subscription_services"
    computer_repair = "computer_repair"
    fuel = "fuel"
    uncategorized_expenses = "uncategorized_expenses"
    other = "other"

class PaginateInvoice(PaginateResponse):
    items: List[Any]