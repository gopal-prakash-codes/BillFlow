import datetime
import uuid

from sqlalchemy import FLOAT, Boolean, Column, DateTime, String

from app.db.session import Base, engine


class PayementDetails(Base):
    __tablename__ = "payment_details"

    id = Column(String(255), default=str(uuid.uuid4()), primary_key=True)
    type = Column(Boolean, default=False, nullable=False)
    invoice_number = Column(String(255), nullable=True)
    account = Column(String(255), nullable=True)
    amount = Column(FLOAT(precision=32, decimal_return_scale=None))
    account_number = Column(String(255), nullable=True)
    vendor = Column(String(255), nullable=True)
    date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=True, default=datetime.datetime.now)
    updated_at = Column(DateTime, nullable=True)


Base.metadata.create_all(bind=engine)

                              
