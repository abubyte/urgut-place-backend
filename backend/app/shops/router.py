from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select
from typing import List, Optional

from app.db.session import get_session
from app.models.shop import Shop
from app.schemas.shop import ShopCreate, ShopRead
from app.auth.dependencies import get_admin_user, get_current_user
from app.models.user import User

router = APIRouter(prefix="/shops", tags=["shops"])

@router.post("", response_model=ShopRead)
async def create_shop(
    shop_data: ShopCreate,
    current_user: User = Depends(get_admin_user),
    session: Session = Depends(get_session)
):
    """Create a new shop (admin only)."""
    shop = Shop(**shop_data.model_dump())
    session.add(shop)
    session.commit()
    session.refresh(shop)
    return shop

@router.get("", response_model=List[ShopRead])
async def list_shops(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),  # Auth required, but any user
    category_id: Optional[int] = Query(None, description="Filter by category ID"),
    skip: int = Query(0, ge=0, description="Number of shops to skip (pagination)"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of shops to return"),
):
    """List all shops with optional filtering and pagination (all users)."""
    query = select(Shop)

    # Filter by category_id if provided
    if category_id is not None:
        query = query.where(Shop.category_id == category_id)

    # Sort by rating (descending)
    query = query.order_by(Shop.rating.desc())

    # Pagination
    query = query.offset(skip).limit(limit)

    shops = session.exec(query).all()
    return shops