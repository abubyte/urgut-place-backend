from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class Category(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)
    icon_url: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)