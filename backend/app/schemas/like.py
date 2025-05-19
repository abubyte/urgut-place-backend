from pydantic import BaseModel
from datetime import datetime


class LikeCreate(BaseModel):
    shop_id: int


class LikeRead(BaseModel):
    id: int
    user_id: int
    shop_id: int
    created_at: datetime

    class Config:
        from_attributes = True