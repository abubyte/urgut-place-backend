from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime
import json


class Shop(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    name: str
    work_time: str
    description: str
    category_id: int = Field(foreign_key="category.id")
    seller_phone: str = Field(index=True)
    image_urls_json: str = Field(default="[]", nullable=True)
    rating: float = Field(default=0.0)
    rating_count: int = Field(default=0)
    like_count: int = Field(default=0)
    location_lat: float
    location_long: float
    location_str: str
    is_featured: bool = Field(default=False)
    expiration_months: int = Field(default=12)
    expires_at: Optional[datetime] = Field(default=None, nullable=True)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    @property
    def image_urls(self) -> List[str]:
        """Return the list of image URLs."""
        return json.loads(self.image_urls_json or "[]")

    @image_urls.setter
    def image_urls(self, values: List[str]):
        """Set the image URLs from a list."""
        self.image_urls_json = json.dumps(values)

    @property
    def is_expired(self) -> bool:
        """Check if shop has expired based on expires_at date."""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at
    
    @property
    def is_available(self) -> bool:
        """Check if shop is both active and not expired."""
        return self.is_active and not self.is_expired