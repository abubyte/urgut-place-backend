from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime


class Shop(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)

    name: str
    work_time: str  # e.g. "08:00 - 22:00"
    description: Optional[str] = None

    images: Optional[List[str]] = Field(default_factory=list, sa_column_kwargs={"nullable": True})
    category_id: int = Field(foreign_key="category.id")
    seller_id: int = Field(foreign_key="seller.id")

    rating: float = Field(default=0.0)
    rating_count: int = Field(default=0)

    location_lat: float
    location_long: float
    location_str: str

    is_featured: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
