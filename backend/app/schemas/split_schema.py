from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class PersonSplitSchema(BaseModel):
    person_id: str
    person_name: str
    items: List[Dict[str, Any]]
    subtotal: float
    tax_share: float
    service_charge_share: float
    discount_share: float
    total: float


class SplitCalculationRequestSchema(BaseModel):
    bill_id: str
    participants: List[str]
    calculation_method: str = "proportional"


class SplitCalculationResponseSchema(BaseModel):
    success: bool
    message: str
    calculation: Optional[Dict[str, Any]] = None
