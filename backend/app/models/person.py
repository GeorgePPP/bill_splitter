from typing import Optional
from pydantic import BaseModel


class Person(BaseModel):
    id: Optional[str] = None
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None


class PersonAssignment(BaseModel):
    person_id: str
    person_name: str
    assigned_items: list[str]  # List of item names assigned to this person
    subtotal: float
    tax_share: float
    total: float
