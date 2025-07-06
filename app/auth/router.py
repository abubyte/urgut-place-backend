import json
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select
from sqlalchemy import func
from datetime import datetime, timedelta
import random
import string
from app.auth.email_client import EmailClient
from app.auth.eskiz_client import EskizClient
from app.db.session import get_session
from app.models.user import User
from app.schemas.user import (
    UserCreate, UserResponse, UserVerifyRequest
)

from app.core.security import create_access_token, get_password_hash, create_tokens, verify_token
from app.core.config import settings
from app.core.rate_limit import rate_limit
from app.core.image_service import ImageService
import logging
import re

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])
image_service = ImageService()

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@rate_limit(times=5, minutes=60)
async def register_user(
    user_data: UserCreate = Depends(UserCreate.as_form),
    image: UploadFile = File(None),
    session: Session = Depends(get_session)
):
    """Register a new user with optional profile image."""
    try:
        # Check if user with same login exists
        existing_user = session.exec(
            select(User).where(User.login == user_data.login)
        ).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this login already exists"
            )

        # Create new user
        user_dict = user_data.model_dump()
        user_dict.update({
            "hashed_password": get_password_hash(user_dict.pop("password")),
        })
        
        user = User(**user_dict)
        session.add(user)
        session.commit()
        session.refresh(user)

        # Handle profile image if provided
        if image:
            image_path = image_service.get_image_url(await image_service.save_image(image, "users"))
            user.image_url = image_path
            session.add(user)
            session.commit()
            session.refresh(user)

        return UserResponse(
            message="User registered successfully. Please verify your account.",
            user=user
        )
    except Exception as e:
        logger.error(f"Error registering user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error registering user: {str(e)}"
        )

@router.post("/send-verification", response_model=dict)
@rate_limit(times=3, minutes=15)
async def send_verification_code(
    login: str = Form(...),
    session: Session = Depends(get_session)
):
    """Send verification code to user's phone/email."""
    user = session.exec(
        select(User).where(User.login == login)
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Create verification code
    verification_code = ''.join(random.choices(string.digits, k=6))
    verification_expires = datetime.utcnow() + timedelta(minutes=15)

    user.verification_code = verification_code
    user.verification_code_expires = verification_expires

    session.add(user)
    session.commit()
    session.refresh(user)

    # Send verification code
    logger.info(f"Verification code for user {user.id}: {verification_code}")
    if re.match(r"^\+998\d{9}$", login):
        EskizClient().send_sms(phone=login.removeprefix("+"), message='Bu Eskiz dan test')
    elif re.match(r"^[^@]+@[^@]+\.[^@]+$", login):
        subject = "Tasdiqlash kodi"
        body = f"UrgutPlease uchun tasdiqlash kodi: {verification_code}"
        EmailClient().send_email(login, subject, body)
        
    return {"message": "Verification code sent successfully. Please check your phone or email."}


@router.post("/verify", response_model=dict, status_code=status.HTTP_200_OK)
@rate_limit(times=3, minutes=15)
async def verify_user(
    verify_data: UserVerifyRequest = Depends(UserVerifyRequest.as_form),
    session: Session = Depends(get_session)
):
    """Verify user's phone/email."""
    user = session.exec(
        select(User).where(User.login == verify_data.login)
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already verified"
        )
    
    if not user.verification_code or not user.verification_code_expires:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No verification code found"
        )
    
    if datetime.utcnow() > user.verification_code_expires:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification code expired"
        )
    
    if user.verification_code != verify_data.code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification code"
        )
    
    user.is_verified = True
    user.verification_code = None
    user.verification_code_expires = None
    session.add(user)
    session.commit()
    session.refresh(user)
    
    return {"message": "User verified successfully"}
        

@router.post("/login", response_model=dict)
@rate_limit(times=5, minutes=15)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session)
):
    """Login user and return access and refresh tokens."""
    user = session.exec(
        select(User).where(User.login == form_data.username)
    ).first()
    
    if not user or not user.verify_password(form_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect login or password"
        )
    
    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Please verify your account first"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is deactivated"
        )
    
    # Update last login
    user.last_login = datetime.utcnow()
    session.add(user)
    session.commit()
    
    # Create both access and refresh tokens
    access_token, refresh_token = create_tokens(data={"sub": user.login})
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

@router.post("/refresh", response_model=dict)
@rate_limit(times=5, minutes=15)
async def refresh_token(
    refresh_token: str,
    session: Session = Depends(get_session)
):
    """Get a new access token using refresh token."""
    username = verify_token(refresh_token)
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    user = session.exec(
        select(User).where(User.login == username)
    ).first()
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    # Create new access token
    access_token = create_access_token(data={"sub": user.login})
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

@router.patch("/reset-password", response_model=dict, status_code=status.HTTP_201_CREATED)
@rate_limit(times=3, minutes=60)
async def reset_password(
    login: str = Form(...),
    new_password: str = Form(...),
    verification_code: str = Form(...),
    session: Session = Depends(get_session)
):
    """Update user's password."""
    try:
        # Check if user with same login exists
        user = session.exec(
            select(User).where(User.login == login)
        ).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User not found"
            )

        # Check if user is verified
        if not user.is_verified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is not verified"
            )
        
        # Check verification code
        if not user.verification_code or not user.verification_code_expires:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No verification code found"
            )
        
        # Check if verification code is expired
        if datetime.utcnow() > user.verification_code_expires:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Verification code expired"
            )
        # Check if verification code matches
        if user.verification_code != verification_code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid verification code"
            )
            
        # Validate new password
        if new_password is not None:
            if not re.search(r'[A-Z]', new_password):
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail='Password must contain at least one uppercase letter'
                )
            if not re.search(r'[a-z]', new_password):
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail='Password must contain at least one lowercase letter'
                )
            if not re.search(r'\d', new_password):
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail='Password must contain at least one number'
                )
            if len(new_password) < 8:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail='Password must be at least 8 characters long'
                )

        user.update_password(new_password)
        user.verification_code = None
        user.verification_code_expires = None
        
        session.add(user)
        session.commit()
        session.refresh(user)
        
        message = {"message": "Password reset successfully"}

        return  message
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resetting password: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error resetting password: {str(e)}"
        )
