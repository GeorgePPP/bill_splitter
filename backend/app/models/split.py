from typing import List, Dict
from pydantic import BaseModel


class PersonSplit(BaseModel):
    person_id: str
    person_name: str
    items: List[Dict[str, any]]  # List of assigned items with details
    subtotal: float
    tax_share: float
    service_charge_share: float
    discount_share: float
    total: float


class SplitCalculation(BaseModel):
    bill_id: str
    participants: List[str]  # Person IDs
    person_splits: List[PersonSplit]
    total_bill: float
    total_tax: float
    total_service_charge: float
    total_discount: float
    net_total: float
    calculation_method: str = "proportional"
