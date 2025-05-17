from sqlmodel import SQLModel, Field
from datetime import datetime


class Like(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)

    user_id: int = Field(foreign_key="user.id")
    shop_id: int = Field(foreign_key="shop.id")

    created_at: datetime = Field(default_factory=datetime.utcnow)