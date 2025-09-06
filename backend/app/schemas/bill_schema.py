from typing import List, Optional
from pydantic import BaseModel
from .receipt_schema import ReceiptDataSchema
from .person_schema import PersonResponseSchema


class BillItemAssignmentSchema(BaseModel):
    item_name: str
    quantity: int
    unit_price: float
    total: float
    assigned_to: Optional[str] = None


class BillSplitCreateSchema(BaseModel):
    receipt_data: ReceiptDataSchema
    participants: List[str]  # Person IDs
    item_assignments: List[BillItemAssignmentSchema]
    tax_distribution: str = "proportional"
    service_charge_distribution: str = "proportional"
    discount_distribution: str = "proportional"


class BillSplitResponseSchema(BaseModel):
    id: str
    receipt_data: ReceiptDataSchema
    participants: List[PersonResponseSchema]
    item_assignments: List[BillItemAssignmentSchema]
    tax_distribution: str
    service_charge_distribution: str
    discount_distribution: str
    created_at: str
    updated_at: str
