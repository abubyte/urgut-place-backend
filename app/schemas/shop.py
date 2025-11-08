from pydantic import BaseModel, computed_field, field_validator, Field as PydanticField
from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import Form
import json
from sqlmodel import Field

class ShopCreate(BaseModel):
    name: str
    description: str
    category_id: int
    seller_phones: List[str]
    location_lat: float
    location_long: float
    sector: int
    number: int
    sale_type: str = "retail"  # wholesale, retail, both
    logo_url: Optional[str] = None
    social_networks: List[Dict[str, str]] = []
    expiration_months: int = Field(default=12, ge=1, le=120)

    @field_validator('seller_phones')
    @classmethod
    def validate_seller_phones(cls, v: List[str]) -> List[str]:
        if len(v) > 5:
            raise ValueError('Maximum 5 phone numbers allowed')
        if len(v) == 0:
            raise ValueError('At least one phone number is required')
        return v

    @field_validator('social_networks')
    @classmethod
    def validate_social_networks(cls, v: List[Dict[str, str]]) -> List[Dict[str, str]]:
        if len(v) > 3:
            raise ValueError('Maximum 3 social networks allowed')
        for network in v:
            if 'type' not in network or 'url' not in network:
                raise ValueError('Each social network must have type and url')
        return v

    @field_validator('sale_type')
    @classmethod
    def validate_sale_type(cls, v: str) -> str:
        if v not in ['wholesale', 'retail', 'both']:
            raise ValueError('sale_type must be one of: wholesale, retail, both')
        return v

    @classmethod
    def as_form(
        cls,
        name: str = Form(...),
        description: str = Form(...),
        category_id: int = Form(...),
        seller_phones: str = Form(...),  # JSON string
        location_lat: float = Form(...),
        location_long: float = Form(...),
        sector: int = Form(...),
        number: int = Form(...),
        sale_type: str = Form(default="retail"),
        logo_url: Optional[str] = Form(default=None),
        social_networks: str = Form(default="[]"),  # JSON string
        expiration_months: int = Form(default=12),
    ):
        # Parse JSON strings
        try:
            seller_phones_list = json.loads(seller_phones) if seller_phones else []
        except json.JSONDecodeError:
            raise ValueError('seller_phones must be a valid JSON array')
        
        try:
            social_networks_list = json.loads(social_networks) if social_networks else []
        except json.JSONDecodeError:
            raise ValueError('social_networks must be a valid JSON array')

        return cls(
            name=name,
            description=description,
            category_id=category_id,
            seller_phones=seller_phones_list,
            location_lat=location_lat,
            location_long=location_long,
            sector=sector,
            number=number,
            sale_type=sale_type,
            logo_url=logo_url,
            social_networks=social_networks_list,
            expiration_months=expiration_months
        )

class ShopRead(BaseModel):
    id: int
    name: str
    description: str
    category_id: int
    image_urls: Optional[List[str]] = None
    seller_phones: List[str]
    rating: float
    rating_count: int
    like_count: int
    location_lat: float
    location_long: float
    sector: int
    number: int
    sale_type: str
    logo_url: Optional[str] = None
    social_networks: List[Dict[str, str]] = []
    is_featured: bool
    expiration_months: int
    expires_at: Optional[datetime]
    is_active: bool
    is_expired: bool
    is_available: bool
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_shop(cls, shop):
        """Create ShopRead from Shop instance, properly handling JSON properties."""
        return cls(
            id=shop.id,
            name=shop.name or '',
            description=shop.description or '',
            category_id=shop.category_id,
            image_urls=shop.image_urls or [],
            seller_phones=shop.seller_phones or [],
            rating=shop.rating,
            rating_count=shop.rating_count,
            like_count=shop.like_count,
            location_lat=shop.location_lat,
            location_long=shop.location_long,
            sector=shop.sector if shop.sector is not None else 0,
            number=shop.number if shop.number is not None else 0,
            sale_type=shop.sale_type or 'retail',
            logo_url=shop.logo_url,
            social_networks=shop.social_networks or [],
            is_featured=shop.is_featured,
            expiration_months=shop.expiration_months,
            expires_at=shop.expires_at,
            is_active=shop.is_active,
            is_expired=shop.is_expired,
            is_available=shop.is_available,
            created_at=shop.created_at,
            updated_at=shop.updated_at,
        )

    class Config:
        from_attributes = True

class ShopUpdate(BaseModel):
    name: str
    description: str
    category_id: int
    seller_phones: List[str]
    location_lat: float
    location_long: float
    sector: int
    number: int
    sale_type: str = "retail"
    logo_url: Optional[str] = None
    social_networks: List[Dict[str, str]] = []
    expiration_months: int = Field(default=12, ge=1, le=120)

    @field_validator('seller_phones')
    @classmethod
    def validate_seller_phones(cls, v: List[str]) -> List[str]:
        if len(v) > 5:
            raise ValueError('Maximum 5 phone numbers allowed')
        if len(v) == 0:
            raise ValueError('At least one phone number is required')
        return v

    @field_validator('social_networks')
    @classmethod
    def validate_social_networks(cls, v: List[Dict[str, str]]) -> List[Dict[str, str]]:
        if len(v) > 3:
            raise ValueError('Maximum 3 social networks allowed')
        for network in v:
            if 'type' not in network or 'url' not in network:
                raise ValueError('Each social network must have type and url')
        return v

    @field_validator('sale_type')
    @classmethod
    def validate_sale_type(cls, v: str) -> str:
        if v not in ['wholesale', 'retail', 'both']:
            raise ValueError('sale_type must be one of: wholesale, retail, both')
        return v

    @classmethod
    def as_form(
        cls,
        name: str = Form(...),
        description: str = Form(...),
        category_id: int = Form(...),
        seller_phones: str = Form(...),  # JSON string
        location_lat: float = Form(...),
        location_long: float = Form(...),
        sector: int = Form(...),
        number: int = Form(...),
        sale_type: str = Form(default="retail"),
        logo_url: Optional[str] = Form(default=None),
        social_networks: str = Form(default="[]"),  # JSON string
        expiration_months: int = Form(default=12),
    ):
        # Parse JSON strings
        try:
            seller_phones_list = json.loads(seller_phones) if seller_phones else []
        except json.JSONDecodeError:
            raise ValueError('seller_phones must be a valid JSON array')
        
        try:
            social_networks_list = json.loads(social_networks) if social_networks else []
        except json.JSONDecodeError:
            raise ValueError('social_networks must be a valid JSON array')

        return cls(
            name=name,
            description=description,
            category_id=category_id,
            seller_phones=seller_phones_list,
            location_lat=location_lat,
            location_long=location_long,
            sector=sector,
            number=number,
            sale_type=sale_type,
            logo_url=logo_url,
            social_networks=social_networks_list,
            expiration_months=expiration_months 
        )
