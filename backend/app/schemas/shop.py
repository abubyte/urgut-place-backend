from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

class ShopCreate(BaseModel):
    name: str
    work_time: str
    description: Optional[str] = None
    images: Optional[List[str]] = None
    category_id: int
    seller_phone: str
    location_lat: float
    location_long: float
    location_str: str
    is_featured: bool = False

class ShopRead(BaseModel):
    id: int
    name: str
    work_time: str
    description: Optional[str]
    images: Optional[List[str]]
    category_id: int
    seller_phone: str
    rating: float
    rating_count: int
    like_count: int
    location_lat: float
    location_long: float
    location_str: str
    is_featured: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ShopUpdate(BaseModel):
    name: Optional[str] = None
    work_time: Optional[str] = None
    description: Optional[str] = None
    images: Optional[List[str]] = None
    category_id: Optional[int] = None
    seller_phone: Optional[str] = None
    location_lat: Optional[float] = None
    location_long: Optional[float] = None
    location_str: Optional[str] = None