from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List

from app.db.session import get_session
from app.models.like import Like
from app.models.shop import Shop
from app.schemas.like import LikeCreate, LikeRead
from app.auth.dependencies import get_current_user
from app.models.user import User, UserRole

router = APIRouter(prefix="/likes", tags=["likes"])

@router.post("", response_model=LikeRead)
async def create_like(
    like_data: LikeCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Create a like for a shop."""

    existing_like = session.exec(
        select(Like).where(Like.user_id == current_user.id, Like.shop_id == like_data.shop_id)
    ).first()
    if existing_like:
        raise HTTPException(status_code=400, detail="You already liked this shop")

    like = Like(user_id=current_user.id, shop_id=like_data.shop_id)
    session.add(like)
    
    shop = session.exec(select(Shop).where(Shop.id == like_data.shop_id)).first()
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")
    shop.like_count += 1
   
    session.add(shop)
    session.commit()
    session.refresh(like)
    return like

@router.get("", response_model=List[LikeRead])
async def list_likes(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """List a user's likes (self or admin)."""
    if current_user.role == UserRole.admin:
        likes = session.exec(select(Like)).all()
    else:
        likes = session.exec(select(Like).where(Like.user_id == current_user.id)).all()
    return likes

@router.delete("/{like_id}")
async def delete_like(
    like_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Delete a like (self or admin)."""
    like = session.exec(select(Like).where(Like.id == like_id)).first()
    if not like:
        raise HTTPException(status_code=404, detail="Like not found")
    if like.user_id != current_user.id and current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Not authorized to delete this like")
    session.delete(like)
    
    shop = session.exec(select(Shop).where(Shop.id == like.shop_id)).first()
    if shop:
        shop.like_count -= 1
        session.add(shop)
        
    session.commit()
    return {"message": "Like deleted"}