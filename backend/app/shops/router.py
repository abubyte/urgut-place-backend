from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from typing import List, Optional
from datetime import datetime

from app.db.session import get_session
from app.models.shop import Shop
from app.schemas.shop import ShopCreate, ShopRead, ShopUpdate
from app.auth.dependencies import get_admin_user, get_current_user
from app.models.user import User
from app.models.category import Category

router = APIRouter(prefix="/shops", tags=["shops"])

@router.post("", response_model=ShopRead)
async def create_shop(
    shop_data: ShopCreate,
    current_user: User = Depends(get_admin_user),
    session: Session = Depends(get_session)
):
    """Create a new shop (admin only)."""
    
    category = session.exec(select(Category).where(Category.id == shop_data.category_id)).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    shop = Shop(**shop_data.model_dump())
    session.add(shop)
    session.commit()
    session.refresh(shop)
    return shop

@router.get("", response_model=List[ShopRead])
async def list_shops(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    category_id: Optional[int] = Query(None, description="Filter by category ID"),
    skip: int = Query(0, ge=0, description="Number of shops to skip (pagination)"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of shops to return"),
):
    """List all shops with optional filtering and pagination (all users)."""
    query = select(Shop)
    if category_id is not None:
        query = query.where(Shop.category_id == category_id)
    query = query.order_by(Shop.rating.desc()).offset(skip).limit(limit)
    shops = session.exec(query).all()
    return shops

@router.get("/{shop_id}", response_model=ShopRead)
async def get_shop(
    shop_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Get a shop by ID (all users)."""
    shop = session.exec(select(Shop).where(Shop.id == shop_id)).first()
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")
    return shop

@router.put("/{shop_id}", response_model=ShopRead)
async def update_shop(
    shop_id: int,
    shop_data: ShopUpdate,
    current_user: User = Depends(get_admin_user),
    session: Session = Depends(get_session)
):
    """Update a shop (admin only)."""
    shop = session.exec(select(Shop).where(Shop.id == shop_id)).first()
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")
    
    update_data = shop_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(shop, key, value)
    
    shop.updated_at = datetime.utcnow()
    
    session.add(shop)
    session.commit()
    session.refresh(shop)
    return shop

@router.delete("/{shop_id}")
async def delete_shop(
    shop_id: int,
    current_user: User = Depends(get_admin_user),
    session: Session = Depends(get_session)
):
    """Delete a shop (admin only)."""
    shop = session.exec(select(Shop).where(Shop.id == shop_id)).first()
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")
    session.delete(shop)
    session.commit()
    return {"message": "Shop deleted"}