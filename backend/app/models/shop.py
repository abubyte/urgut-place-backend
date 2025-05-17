from sqlmodel import SQLModel, Field
from typing import Optional, List
from datetime import datetime
from sqlalchemy import JSON


class Shop(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    name: str
    work_time: str  # e.g. "08:00 - 22:00"
    description: Optional[str] = None
    images: Optional[List[str]] = Field(default=None, sa_type=JSON, sa_column_kwargs={"nullable": True})
    category_id: int = Field(foreign_key="category.id")
    seller_phone: str = Field(index=True)  # Phone number of the seller
    rating: float = Field(default=0.0)
    rating_count: int = Field(default=0)
    location_lat: float
    location_long: float
    location_str: str
    is_featured: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)