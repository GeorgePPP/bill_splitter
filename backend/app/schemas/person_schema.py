from typing import Optional, List
from pydantic import BaseModel


class PersonCreateSchema(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None


class PersonResponseSchema(BaseModel):
    id: str
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None


class PersonListResponseSchema(BaseModel):
    participants: List[PersonResponseSchema]
    total: int
