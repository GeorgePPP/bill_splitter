from typing import List, Optional
from pydantic import BaseModel
from .receipt import ReceiptData
from .person import Person


class BillItemAssignment(BaseModel):
    item_name: str
    quantity: int
    unit_price: float
    total: float
    assigned_to: Optional[str] = None  # Person ID


class BillSplit(BaseModel):
    id: Optional[str] = None
    receipt_data: ReceiptData
    participants: List[Person]
    item_assignments: List[BillItemAssignment]
    tax_distribution: str = "proportional"  # "proportional" or "equal"
    service_charge_distribution: str = "proportional"
    discount_distribution: str = "proportional"
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class SplitResult(BaseModel):
    bill_split_id: str
    person_assignments: List[dict]  # Will contain PersonAssignment objects
    total_bill: float
    total_tax: float
    total_service_charge: float
    total_discount: float
    net_total: float
