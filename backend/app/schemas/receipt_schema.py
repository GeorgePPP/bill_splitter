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
    total_price: float  # Changed from 'total' to 'total_price' to match requirements


class TaxOrChargeSchema(BaseModel):
    name: str
    amount: float
    percent: Optional[float] = None


class ReceiptDataSchema(BaseModel):
    receipt_number: str
    date: str
    time: str
    store: StoreInfoSchema
    items: List[BillItemSchema]
    subtotal: float
    taxes_or_charges: List[TaxOrChargeSchema] = []  # New field to replace individual tax/service_charge
    grand_total: float  # Changed from 'total_amount' to 'grand_total' to match requirements
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
