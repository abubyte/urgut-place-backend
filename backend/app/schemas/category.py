from pydantic import BaseModel
from typing import Optional


class CategoryCreate(BaseModel):
    name: str
    description: Optional[str] = None


class CategoryRead(BaseModel):
    id: int
    name: str
    description: Optional[str]

    class Config:
        from_attributes = True