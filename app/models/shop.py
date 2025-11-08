from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List, Dict, Any
from datetime import datetime
import json


class Shop(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    name: str
    description: str
    category_id: int = Field(foreign_key="category.id")
    seller_phones_json: str = Field(default="[]", nullable=True)
    image_urls_json: str = Field(default="[]", nullable=True)
    rating: float = Field(default=0.0)
    rating_count: int = Field(default=0)
    like_count: int = Field(default=0)
    location_lat: float
    location_long: float
    sector: int
    number: int
    sale_type: str = Field(default="retail")  # wholesale, retail, both
    logo_url: Optional[str] = Field(default=None, nullable=True)
    social_networks_json: str = Field(default="[]", nullable=True)
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
    def seller_phones(self) -> List[str]:
        """Return the list of seller phone numbers."""
        return json.loads(self.seller_phones_json or "[]")

    @seller_phones.setter
    def seller_phones(self, values: List[str]):
        """Set the seller phone numbers from a list."""
        self.seller_phones_json = json.dumps(values)

    @property
    def social_networks(self) -> List[Dict[str, str]]:
        """Return the list of social networks."""
        return json.loads(self.social_networks_json or "[]")

    @social_networks.setter
    def social_networks(self, values: List[Dict[str, str]]):
        """Set the social networks from a list."""
        self.social_networks_json = json.dumps(values)

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