from pydantic import BaseModel, EmailStr, constr, validator
from typing import Annotated, Optional
from pydantic import StringConstraints
from datetime import datetime
from app.models.user import UserRole
from fastapi import Form
import re
from app.core.image_service import ImageService

# Phone number validation regex
PHONE_REGEX = r'^\+998\d{9}$'
EMAIL_REGEX = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
LOGIN_REGEX = r'^(?:\+998\d{9}|[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})$'

# Authentication schemas

class UserVerifyRequest(BaseModel):
    login: Annotated[str, StringConstraints(pattern=LOGIN_REGEX)]
    code: Annotated[str, StringConstraints(min_length=4, max_length=6)]

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
            password=password
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
    full_image_url: Optional[str]  # Full URL for the image
    created_at: datetime
    last_login: Optional[datetime]

    class Config:
        from_attributes = True

    def __init__(self, **data):
        super().__init__(**data)
        if hasattr(self, 'image_url') and self.image_url:
            image_service = ImageService()
            self.full_image_url = image_service.get_image_url(self.image_url)
        else:
            self.full_image_url = None

class UserUpdate(BaseModel):
    firstname: Optional[Annotated[str, StringConstraints(min_length=2, max_length=50)]] = None
    lastname: Optional[Annotated[str, StringConstraints(min_length=2, max_length=50)]] = None
    phone: Optional[Annotated[str, StringConstraints(pattern=PHONE_REGEX)]] = None
    email: Optional[EmailStr] = None
    password: Optional[Annotated[str, StringConstraints(min_length=8)]] = None

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

    @classmethod
    def as_form(
        cls,
        firstname: Optional[str] = Form(None),
        lastname: Optional[str] = Form(None),
        phone: Optional[str] = Form(None),
        email: Optional[str] = Form(None),
        password: Optional[str] = Form(None),
    ):
        return cls(
            firstname=firstname,
            lastname=lastname,
            phone=phone,
            email=email,
            password=password
        )

class UserResponse(BaseModel):
    message: str
    user: UserRead

class UserListResponse(BaseModel):
    total: int
    users: list[UserRead]
    page: int
    size: int