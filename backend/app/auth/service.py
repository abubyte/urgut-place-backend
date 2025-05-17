from datetime import datetime, timedelta
from typing import Optional
from jose import jwt
from sqlmodel import Session, select
from fastapi import HTTPException
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# JWT Settings
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

from app.models.user import User, UserRole
from app.models.verification import VerificationCode
from app.schemas.user import UserCreate

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Generate a JWT token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_code_and_get_user(login: str, code: str, session: Session) -> User:
    """Verify the code and return or create a user."""
    # Find the latest valid verification code
    statement = select(VerificationCode).where(
        VerificationCode.login == login,
        VerificationCode.code == code,
        VerificationCode.is_used == False,
        VerificationCode.expires_at > datetime.utcnow()
    ).order_by(VerificationCode.created_at.desc())

    verification = session.exec(statement).first()

    if not verification:
        raise HTTPException(status_code=400, detail="Invalid or expired verification code")
    
    # Mark the code as used
    verification.is_used = True
    session.add(verification)

    # Check if the user already exists
    user = session.exec(select(User).where(User.login == login)).first()

    if not user:
        # Create a new user if not exists
        user_data = UserCreate(
            firstname="Default",
            lastname="User",
            login=login,
            phone=login if "+" in login else None,
            email=login if "@" in login else None,
            role=UserRole.client,
            image_url=None
        )
        user = User(**user_data.model_dump())
        user.is_verified = True
        session.add(user)
    
    session.commit()
    return user