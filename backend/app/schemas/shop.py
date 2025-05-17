from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
import re


class ShopCreate(BaseModel):
    name: str
    work_time: str  # e.g., "08:00 - 22:00"
    description: Optional[str] = None
    images: Optional[List[str]] = None
    category_id: int
    seller_phone: str = Field(..., description="Uzbekistan phone number, e.g., +998901234567")
    location_lat: float
    location_long: float
    location_str: str
    is_featured: Optional[bool] = False

    @validator("seller_phone")
    def validate_seller_phone(cls, value):
        """Ensure seller_phone is a valid Uzbekistan phone number."""
        phone_pattern = r"^\+998\d{9}$"
        if not re.match(phone_pattern, value):
            raise ValueError("Invalid Uzbekistan phone number. Must be +998 followed by 9 digits.")
        return value

    @validator("work_time")
    def validate_work_time(cls, value):
        """Ensure work_time is in HH:MM - HH:MM format."""
        time_pattern = r"^\d{2}:\d{2} - \d{2}:\d{2}$"
        if not re.match(time_pattern, value):
            raise ValueError("Work time must be in format 'HH:MM - HH:MM', e.g., '08:00 - 22:00'.")
        return value


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
    location_lat: float
    location_long: float
    location_str: str
    is_featured: bool
    created_at: datetime

    class Config:
        from_attributes = True