from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.db.session import get_session
from app.models.like import Like
from app.schemas.like import LikeCreate, LikeRead
from app.auth.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/likes", tags=["likes"])

@router.post("", response_model=LikeRead)
async def create_like(
    like_data: LikeCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Create a like for a shop (clients only)."""
    if current_user.role != "client":
        raise HTTPException(status_code=403, detail="Only clients can like shops")

    # Check if the user already liked this shop
    existing_like = session.exec(
        select(Like).where(Like.user_id == current_user.id, Like.shop_id == like_data.shop_id)
    ).first()
    if existing_like:
        raise HTTPException(status_code=400, detail="You already liked this shop")

    like = Like(user_id=current_user.id, shop_id=like_data.shop_id)
    session.add(like)
    session.commit()
    session.refresh(like)
    return like