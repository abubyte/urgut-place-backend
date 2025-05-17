from typing import Optional
from pydantic import BaseModel
from enum import Enum
from app.models.user import UserRole


class UserCreate(BaseModel):
    firstname: str
    lastname: str
    login: str
    phone: Optional[str]
    email: Optional[str]
    image_url: Optional[str] = None
    role: Optional[UserRole] = UserRole.client


class UserRead(BaseModel):
    id: int
    firstname: str
    lastname: str
    login: str
    phone: Optional[str]
    email: Optional[str]
    image_url: Optional[str]
    role: UserRole
    is_verified: bool

    class Config:
        from_attributes = True
    
class UserAuthRequest(BaseModel):
    login: str

class UserVerifyRequest(BaseModel):
    login: str
    code: str