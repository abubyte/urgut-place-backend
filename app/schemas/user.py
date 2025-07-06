from pydantic import BaseModel, EmailStr, constr, validator
from typing import Annotated, Optional, List
from pydantic import StringConstraints
from datetime import datetime
from app.models.user import UserRole
from fastapi import Form, UploadFile, File
import re
import json

# Phone number validation regex
PHONE_REGEX = r'^\+998\d{9}$'
EMAIL_REGEX = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
LOGIN_REGEX = r'^(?:\+998\d{9}|[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})$'

# Authentication schemas

class UserVerifyRequest(BaseModel):
    login: Annotated[str, StringConstraints(pattern=LOGIN_REGEX)]
    code: Annotated[str, StringConstraints(min_length=4, max_length=6)]
    
    @classmethod
    def as_form(
        cls,
        login: str = Form(...),
        code: str = Form(...),
    ):
        return cls(login=login, code=code)

class UserCreate(BaseModel):
    firstname: Annotated[str, StringConstraints(min_length=2, max_length=50)]
    lastname: Annotated[str, StringConstraints(min_length=2, max_length=50)]
    login: Annotated[str, StringConstraints(min_length=3, max_length=50)]
    phone: Optional[Annotated[str, StringConstraints(pattern=PHONE_REGEX)]] = None
    email: Optional[EmailStr] = None
    password: Annotated[str, StringConstraints(min_length=8)]

    @validator('login')
    def validate_login(cls, v):
        if not re.match(LOGIN_REGEX, v):
            raise ValueError('Login can only be email or Uzbekistan phone number')
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

    @classmethod
    def as_form(
        cls,
        firstname: str = Form(...),
        lastname: str = Form(...),
        login: str = Form(...),
        phone: Optional[str] = Form(None),
        email: Optional[str] = Form(None),
        password: str = Form(...),
    ):
        return cls(
            firstname=firstname,
            lastname=lastname,
            login=login,
            phone=phone,
            email=email,
            password=password,
        )

class UserRead(BaseModel):
    id: int
    firstname: str
    lastname: str
    login: str
    phone: Optional[str]
    email: Optional[str]
    role: UserRole
    is_verified: bool
    image_url: Optional[str]  
    created_at: datetime
    last_login: Optional[datetime]

    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    firstname: str = Form(...)
    lastname: str = Form(...)
    phone: Optional[str] = Form(None)
    email: Optional[str] = Form(None)

    @classmethod
    def as_form(
        cls,
        firstname: str = Form(...),
        lastname: str = Form(...),
        phone: Optional[str] = Form(None),
        email: Optional[str] = Form(None),
    ):
        return cls(
            firstname=firstname,
            lastname=lastname,
            phone=phone,
            email=email,
        )

class UserResponse(BaseModel):
    message: str
    user: UserRead

class UserListResponse(BaseModel):
    total: int
    users: list[UserRead]
    page: int
    size: int

class UserRoleUpdate(BaseModel):
    role: UserRole

    @classmethod
    def as_form(
        cls,
        role: UserRole = Form(...),
    ):
        return cls(role=role)