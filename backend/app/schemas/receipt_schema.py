from typing import Optional, List
from pydantic import BaseModel


class StoreInfoSchema(BaseModel):
    name: str
    address: Optional[str] = None
    phone: Optional[str] = None


class BillItemSchema(BaseModel):
    name: str
    quantity: int
    unit_price: float
    total: float


class ReceiptDataSchema(BaseModel):
    receipt_number: str
    date: str
    time: str
    store: StoreInfoSchema
    items: List[BillItemSchema]
    subtotal: float
    tax: float
    service_charge: float = 0.0
    discount: float = 0.0
    total_amount: float
    payment_method: str
    transaction_id: Optional[str] = None
    notes: Optional[str] = None


class ReceiptUploadResponse(BaseModel):
    success: bool
    message: str
    receipt_id: Optional[str] = None
    raw_text: Optional[str] = None


class ReceiptProcessResponse(BaseModel):
    success: bool
    message: str
    processed_data: Optional[ReceiptDataSchema] = None
