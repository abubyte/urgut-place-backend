from pydantic import BaseModel, computed_field
from datetime import datetime
from typing import List, Optional
from fastapi import Form
import json
from sqlmodel import Field

class ShopCreate(BaseModel):
    name: str
    work_time: str
    description: str
    category_id: int
    seller_phone: str
    location_lat: float
    location_long: float
    location_str: str
    expiration_months: int = Field(default=12, ge=1, le=120)

    @classmethod
    def as_form(
        cls,
        name: str = Form(...),
        work_time: str = Form(...),
        description: str = Form(...),
        category_id: int = Form(...),
        seller_phone: str = Form(...),
        location_lat: float = Form(...),
        location_long: float = Form(...),
        location_str: str = Form(...),
        expiration_months: int = Form(default=12),
    ):
        return cls(
            name=name,
            work_time=work_time,
            description=description,
            category_id=category_id,
            seller_phone=seller_phone,
            location_lat=location_lat,
            location_long=location_long,
            location_str=location_str,
            expiration_months=expiration_months
        )

class ShopRead(BaseModel):
    id: int
    name: str
    work_time: str
    description: str
    category_id: int
    image_urls: Optional[List[str]] = None
    seller_phone: str
    rating: float
    rating_count: int
    like_count: int
    location_lat: float
    location_long: float
    location_str: str
    is_featured: bool
    expiration_months: int
    expires_at: Optional[datetime]
    is_active: bool
    is_expired: bool
    is_available: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ShopUpdate(BaseModel):
    name: str
    work_time: str
    description: str
    category_id: int
    seller_phone: str
    location_lat: float
    location_long: float
    location_str: str
    expiration_months: int = Field(default=12, ge=1, le=120)

    @classmethod
    def as_form(
        cls,
        name: str = Form(...),
        work_time: str = Form(...),
        description: str = Form(...),
        category_id: int = Form(...),
        seller_phone: str = Form(...),
        location_lat: float = Form(...),
        location_long: float = Form(...),
        location_str: str = Form(...),
        expiration_months: int = Form(default=12),
    ):
        return cls(
            name=name,
            work_time=work_time,
            description=description,
            category_id=category_id,
            seller_phone=seller_phone,
            location_lat=location_lat,
            location_long=location_long,
            location_str=location_str,
            expiration_months=expiration_months 
        )
