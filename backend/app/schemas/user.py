from pydantic import BaseModel, EmailStr, constr, validator
from datetime import datetime
from typing import Optional
from app.models.user import UserRole
import re

# Phone number validation regex
PHONE_REGEX = r'^\+?1?\d{9,15}$'

# Authentication schemas
class UserAuthRequest(BaseModel):
    phone: constr(regex=PHONE_REGEX)
    
    @validator('phone')
    def validate_phone(cls, v):
        if not re.match(PHONE_REGEX, v):
            raise ValueError('Invalid phone number format')
        return v

class UserVerifyRequest(BaseModel):
    phone: constr(regex=PHONE_REGEX)
    code: constr(min_length=4, max_length=6)

class UserCreate(BaseModel):
    firstname: constr(min_length=2, max_length=50)
    lastname: constr(min_length=2, max_length=50)
    login: constr(min_length=3, max_length=50)
    phone: Optional[constr(regex=PHONE_REGEX)] = None
    email: Optional[EmailStr] = None
    password: constr(min_length=8)
    role: UserRole = UserRole.client

    @validator('login')
    def validate_login(cls, v):
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('Login can only contain letters, numbers and underscores')
        return v

    @validator('password')
    def validate_password(cls, v):
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one number')
        return v

class UserRead(BaseModel):
    id: int
    firstname: str
    lastname: str
    login: str
    phone: Optional[str]
    email: Optional[str]
    role: UserRole
    is_verified: bool
    created_at: datetime
    last_login: Optional[datetime]

    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    firstname: Optional[constr(min_length=2, max_length=50)] = None
    lastname: Optional[constr(min_length=2, max_length=50)] = None
    phone: Optional[constr(regex=PHONE_REGEX)] = None
    email: Optional[EmailStr] = None
    password: Optional[constr(min_length=8)] = None
    role: Optional[UserRole] = None

    @validator('password')
    def validate_password(cls, v):
        if v is not None:
            if not re.search(r'[A-Z]', v):
                raise ValueError('Password must contain at least one uppercase letter')
            if not re.search(r'[a-z]', v):
                raise ValueError('Password must contain at least one lowercase letter')
            if not re.search(r'\d', v):
                raise ValueError('Password must contain at least one number')
        return v

class UserResponse(BaseModel):
    message: str
    user: UserRead

class UserListResponse(BaseModel):
    total: int
    users: list[UserRead]
    page: int
    size: int