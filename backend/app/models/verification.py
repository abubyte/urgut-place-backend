from sqlmodel import SQLModel, Field
from datetime import datetime, timedelta
from typing import Optional


class VerificationCode(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    login: str
    code: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime = Field(default_factory=lambda: datetime.utcnow() + timedelta(minutes=5))
    is_used: bool = Field(default=False)

    class Config:
        arbitrary_types_allowed = True