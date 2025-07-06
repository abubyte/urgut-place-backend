from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class RatingCreate(BaseModel):
    shop_id: int
    rating: int = Field(ge=1, le=5)  # Rating between 1 and 5

class RatingRead(BaseModel):
    id: int
    user_id: int
    shop_id: int
    rating: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class RatingUpdate(BaseModel):
    rating: Optional[int] = Field(None, ge=1, le=5)