from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class StoreInfo(BaseModel):
    name: str
    address: Optional[str] = None
    phone: Optional[str] = None


class BillItem(BaseModel):
    name: str
    quantity: int
    unit_price: float
    total_price: float  # Changed from 'total' to 'total_price' to match requirements


class TaxOrCharge(BaseModel):
    name: str
    amount: float
    percent: Optional[float] = None


class ReceiptData(BaseModel):
    receipt_number: str
    date: str
    time: str
    store: StoreInfo
    items: List[BillItem]
    subtotal: float
    taxes_or_charges: List[TaxOrCharge] = []  # New field to replace individual tax/service_charge
    grand_total: float  # Changed from 'total_amount' to 'grand_total' to match requirements
    payment_method: str
    transaction_id: Optional[str] = None
    notes: Optional[str] = None


class Receipt(BaseModel):
    id: Optional[str] = None
    filename: str
    raw_text: str
    processed_data: Optional[ReceiptData] = None
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()
