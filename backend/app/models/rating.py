from sqlmodel import SQLModel, Field
from datetime import datetime

class Rating(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    shop_id: int = Field(foreign_key="shop.id")
    rating: int = Field(ge=1, le=5)  # Rating between 1 and 5
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)