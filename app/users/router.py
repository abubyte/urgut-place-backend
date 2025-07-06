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
    image: UploadFile = File(None),
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
    
    # Update other fields
    for key, value in update_data.items():
        setattr(user, key, value)
    
    # Handle profile image
    if image is not None:
        if user.image_url:
            await image_service.delete_image(user.image_url)
        
        if image:
            image_path = image_service.get_image_url(await image_service.save_image(image, "users"))
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