from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select
from sqlalchemy import func
from datetime import datetime, timedelta
import random
import string
from app.db.session import get_session
from app.models.user import User, UserRole
from app.schemas.user import (
    UserCreate, UserRead, UserUpdate, UserResponse,
    UserListResponse, UserVerifyRequest
)
from app.auth.dependencies import get_current_user, get_admin_user
from app.core.security import create_access_token, get_password_hash
from app.core.config import settings
from app.core.rate_limit import rate_limit
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/users", tags=["users"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@rate_limit(times=5, minutes=60)
async def register_user(
    user_data: UserCreate,
    session: Session = Depends(get_session)
):
    """Register a new user."""
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
        user = User(
            **user_data.model_dump(exclude={'password'}),
            hashed_password=get_password_hash(user_data.password),
            verification_code=verification_code,
            verification_code_expires=verification_expires
        )
        
        session.add(user)
        session.commit()
        session.refresh(user)

        # TODO: Send verification code via SMS/Email
        logger.info(f"Verification code for user {user.id}: {verification_code}")

        return UserResponse(
            message="User registered successfully. Please verify your account.",
            user=user
        )
    except Exception as e:
        logger.error(f"Error registering user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error registering user"
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
    """Login user and return access token."""
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

@router.put("/{user_id}", response_model=UserResponse) # TODO: consider security to change role
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Update a user (self or admin)."""
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
    
    update_data = user_data.model_dump(exclude_unset=True)
    
    # Handle password update
    if "password" in update_data:
        user.update_password(update_data.pop("password"))
    
    # Update other fields
    for key, value in update_data.items():
        setattr(user, key, value)
    
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
    
    session.delete(user)
    session.commit()
    
    return {"message": "User deleted successfully"}