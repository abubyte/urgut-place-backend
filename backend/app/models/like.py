from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime


class Like(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    shop_id: int = Field(foreign_key="shop.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        table_args = {"unique_together": ("user_id", "shop_id")}  # Prevent duplicate likes