# backend/app/schemas/receipt_schema.py
"""
Receipt API schemas for request/response serialization.
"""
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
    total_price: float


class TaxOrChargeSchema(BaseModel):
    name: str
    amount: float
    percent: Optional[float] = None


class ReceiptDataSchema(BaseModel):
    """Schema for receipt data in API requests/responses."""
    receipt_number: str
    date: str
    time: str
    store: StoreInfoSchema
    items: List[BillItemSchema]
    subtotal: float
    taxes_or_charges: List[TaxOrChargeSchema] = []
    grand_total: float
    payment_method: str
    transaction_id: Optional[str] = None
    notes: Optional[str] = None


class ReceiptProcessResponse(BaseModel):
    """Response from receipt processing endpoint."""
    success: bool
    message: str
    processed_data: Optional[ReceiptDataSchema] = None
    raw_text: Optional[str] = None  # OCR text for debugging/reference