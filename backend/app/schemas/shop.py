from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional
from fastapi import Form

class ShopCreate(BaseModel):
    name: str
    work_time: str
    description: Optional[str] = None
    category_id: int
    seller_phone: str
    location_lat: float
    location_long: float
    location_str: str

    @classmethod
    def as_form(
        cls,
        name: str = Form(...),
        work_time: str = Form(...),
        description: Optional[str] = Form(None),
        category_id: int = Form(...),
        seller_phone: str = Form(...),
        location_lat: float = Form(...),
        location_long: float = Form(...),
        location_str: str = Form(...),
    ):
        return cls(
            name=name,
            work_time=work_time,
            description=description,
            category_id=category_id,
            seller_phone=seller_phone,
            location_lat=location_lat,
            location_long=location_long,
            location_str=location_str
        )

class ShopRead(BaseModel):
    id: int
    name: str
    work_time: str
    description: Optional[str]
    image_urls: Optional[List[str]]
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

    def __init__(self, **data):
        super().__init__(**data)
        if hasattr(self, 'images') and self.images:
            from app.core.image_service import ImageService
            image_service = ImageService()
            self.image_urls = [image_service.get_image_url(img) for img in self.images]
        else:
            self.image_urls = []

class ShopUpdate(BaseModel):
    name: Optional[str] = None
    work_time: Optional[str] = None
    description: Optional[str] = None
    category_id: Optional[int] = None
    seller_phone: Optional[str] = None
    location_lat: Optional[float] = None
    location_long: Optional[float] = None
    location_str: Optional[str] = None

    @classmethod
    def as_form(
        cls,
        name: Optional[str] = Form(None),
        work_time: Optional[str] = Form(None),
        description: Optional[str] = Form(None),
        category_id: Optional[int] = Form(None),
        seller_phone: Optional[str] = Form(None),
        location_lat: Optional[float] = Form(None),
        location_long: Optional[float] = Form(None),
        location_str: Optional[str] = Form(None),
    ):
        return cls(
            name=name,
            work_time=work_time,
            description=description,
            category_id=category_id,
            seller_phone=seller_phone,
            location_lat=location_lat,
            location_long=location_long,
            location_str=location_str
        )
