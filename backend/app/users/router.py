from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select
from sqlalchemy import func
from datetime import datetime, timedelta
import random
import string
from app.auth.email_client import EmailClient
from app.auth.eskiz_client import EskizClient
from app.db.session import get_session
from app.models.user import User, UserRole
from app.schemas.user import (
    UserCreate, UserRead, UserUpdate, UserResponse,
    UserListResponse, UserVerifyRequest, UserRoleUpdate
)
from app.auth.dependencies import get_current_user, get_admin_user
from app.core.security import create_access_token, get_password_hash, create_tokens, verify_token
from app.core.config import settings
from app.core.rate_limit import rate_limit
from app.core.image_service import ImageService
import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/users", tags=["users"])
image_service = ImageService()

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@rate_limit(times=5, minutes=60)
async def register_user(
    user_data: UserCreate = Depends(UserCreate.as_form),
    image: Optional[UploadFile] = File(None),
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

        # Create verification code
        verification_code = ''.join(random.choices(string.digits, k=6))
        verification_expires = datetime.utcnow() + timedelta(minutes=15)

        # Create new user
        user_dict = user_data.model_dump()
        user_dict.update({
            "hashed_password": get_password_hash(user_dict.pop("password")),
            "verification_code": verification_code,
            "verification_code_expires": verification_expires
        })
        
        user = User(**user_dict)
        session.add(user)
        session.commit()
        session.refresh(user)

        # Handle profile image if provided
        if image:
            image_path = await image_service.save_image(image, "users")
            user.image_url = image_path
            session.add(user)
            session.commit()
            session.refresh(user)

        # Send verification code
        logger.info(f"Verification code for user {user.id}: {verification_code}")
        if re.match(r"^\+998\d{9}$", user_data.login):
            EskizClient().send_sms(phone=user_data.login.removeprefix("+"), message='Bu Eskiz dan test')
        elif re.match(r"^[^@]+@[^@]+\.[^@]+$", user_data.login):
            subject = "Tasdiqlash kodi"
            body = f"UrgutPlease uchun tasdiqlash kodi: {verification_code}"
            EmailClient().send_email(user_data.login, subject, body)

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

@router.post("/verify", response_model=UserResponse)
@rate_limit(times=3, minutes=15)
async def verify_user(
    verify_data: UserVerifyRequest,
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
    
    return UserResponse(
        message="User verified successfully",
        user=user
    )

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

@router.get("", response_model=UserListResponse)
async def list_users(
    current_user: User = Depends(get_admin_user),
    session: Session = Depends(get_session),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100)
):
    """List all users (admin only)."""
    total = session.exec(select(func.count()).select_from(User)).one()
    users = session.exec(
        select(User)
        .offset(skip)
        .limit(limit)
    ).all()
    
    return UserListResponse(
        total=total,
        users=users,
        page=(skip // limit) + 1,
        size=limit
    )

@router.get("/me", response_model=UserRead)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """Get current user information."""
    return current_user

@router.get("/{user_id}", response_model=UserRead)
async def get_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Get a user by ID (self or admin)."""
    user = session.exec(select(User).where(User.id == user_id)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    if current_user.id != user_id and current_user.role != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this user"
        )
    return user

@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate = Depends(UserUpdate.as_form),
    image: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Update a user with optional profile image (self or admin)."""
    user = session.exec(select(User).where(User.id == user_id)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    if current_user.id != user_id and current_user.role != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this user"
        )
    
    # Update basic fields
    update_data = user_data.model_dump(exclude_unset=True)
    
    # Handle password update
    if "password" in update_data:
        user.update_password(update_data.pop("password"))
    
    # Update other fields
    for key, value in update_data.items():
        setattr(user, key, value)
    
    # Handle profile image
    if image is not None:  # If image field is provided (even if empty)
        # Delete old image if exists
        if user.image_url:
            await image_service.delete_image(user.image_url)
        
        # Save new image if provided
        if image:
            image_path = await image_service.save_image(image, "users")
            user.image_url = image_path
        else:
            user.image_url = None
    
    user.updated_at = datetime.utcnow()
    session.add(user)
    session.commit()
    session.refresh(user)
    
    return UserResponse(
        message="User updated successfully",
        user=user
    )

@router.delete("/{user_id}", response_model=dict)
async def delete_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Delete a user (self or admin)."""
    user = session.exec(select(User).where(User.id == user_id)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
        
    if current_user.id != user_id and current_user.role != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this user"
        )
    
    # Delete profile image if exists
    if user.image_url:
        await image_service.delete_image(user.image_url)
    
    session.delete(user)
    session.commit()
    
    return {"message": "User deleted successfully"}

@router.patch("/{user_id}/role", response_model=UserResponse)
async def update_user_role(
    user_id: int,
    role_data: UserRoleUpdate,
    current_user: User = Depends(get_admin_user),
    session: Session = Depends(get_session)
):
    """Update a user's role (admin only)."""
    user = session.exec(select(User).where(User.id == user_id)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.role = role_data.role
    user.updated_at = datetime.utcnow()
    
    session.add(user)
    session.commit()
    session.refresh(user)
    
    return UserResponse(
        message="User role updated successfully",
        user=user
    )