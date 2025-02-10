from pydantic import BaseModel

from datetime import datetime
from decimal import Decimal


class AddPaymentDetailsPayload(BaseModel):
    account: str
    type: str
    amount: Decimal
    account_number: str
    vendor: str
    date: datetime
    invoice_id: str

class ImageNotFoundEmailPayload(BaseModel):
    invoice_id: str

    class Config:
        use_orm = True
