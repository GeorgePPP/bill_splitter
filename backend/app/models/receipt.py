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
    total: float


class ReceiptData(BaseModel):
    receipt_number: str
    date: str
    time: str
    store: StoreInfo
    items: List[BillItem]
    subtotal: float
    tax: float
    service_charge: float = 0.0
    discount: float = 0.0
    total_amount: float
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
