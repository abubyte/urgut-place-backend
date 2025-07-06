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