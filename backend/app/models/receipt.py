# backend/app/models/receipt.py
"""
Receipt data models for bill splitting.
No persistence-related fields - pure data transfer objects.
"""
from typing import Optional, List
from pydantic import BaseModel


class StoreInfo(BaseModel):
    """Store/restaurant information."""
    name: str
    address: Optional[str] = None
    phone: Optional[str] = None


class BillItem(BaseModel):
    """A single item on the receipt."""
    name: str
    quantity: int
    unit_price: float
    total_price: float


class TaxOrCharge(BaseModel):
    """Tax, service charge, or discount line item."""
    name: str
    amount: float  # Negative for discounts
    percent: Optional[float] = None


class ReceiptData(BaseModel):
    """Complete extracted receipt data."""
    receipt_number: str
    date: str
    time: str
    store: StoreInfo
    items: List[BillItem]
    subtotal: float
    taxes_or_charges: List[TaxOrCharge] = []
    grand_total: float
    payment_method: str
    transaction_id: Optional[str] = None
    notes: Optional[str] = None