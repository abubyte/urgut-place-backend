from sqlmodel import SQLModel, Field
from datetime import datetime


class Seller(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    name: str
    rating: float = Field(default=0.0)
    rating_count: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
