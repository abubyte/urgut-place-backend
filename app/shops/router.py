from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from pydantic import BeforeValidator
from sqlmodel import Session, select, or_, desc, asc
from typing import Annotated, Any, List, Optional, Union
from datetime import datetime
from enum import Enum
from pydantic.json_schema import SkipJsonSchema

from app.db.session import get_session
from app.models.shop import Shop
from app.schemas.shop import ShopCreate, ShopRead, ShopUpdate
from app.auth.dependencies import get_admin_user, get_current_user
from app.models.user import User
from app.models.category import Category
from app.core.image_service import ImageService

router = APIRouter(prefix="/shops", tags=["shops"])
image_service = ImageService()

def empty_str_to_none(v: Any) -> Any:
    if v == "" or v is None:
        return []
    return v

class SortField(str, Enum):
    rating = "rating"
    name = "name"
    created_at = "created_at"
    like_count = "like_count"
    rating_count = "rating_count"

class SortOrder(str, Enum):
    asc = "asc"
    desc = "desc"

@router.post("", response_model=ShopRead)
async def create_shop(
    shop_data: ShopCreate = Depends(ShopCreate.as_form),
    images: List[UploadFile] = File(None),
    current_user: User = Depends(get_admin_user),
    session: Session = Depends(get_session)
):
    """Create a new shop with images (admin only)."""
    try:
        # Validate category
        category = session.exec(select(Category).where(Category.id == shop_data.category_id)).first()
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")
        
        # Create shop
        shop = Shop(**shop_data.model_dump())
        session.add(shop)
        session.commit()
        session.refresh(shop)
        
        # Handle images if provided
        if images:
            image_paths = []
            for image in images:
                image_path = image_service.get_image_url(await image_service.save_image(image, "shops"))
                if image_path:
                    image_paths.append(image_path)
            
            shop.image_urls = image_paths
            session.add(shop)
            session.commit()
            session.refresh(shop)
        
        return shop
    finally:
        session.close()

@router.get("", response_model=List[ShopRead])
async def list_shops(
    session: Session = Depends(get_session),
    # current_user: User = Depends(get_current_user),
    category_id: Optional[int] = Query(None, description="Filter by category ID"),
    search: Optional[str] = Query(None, description="Search in name, description, and location"),
    featured: Optional[bool] = Query(None, description="Filter by featured status"),
    sort_by: SortField = Query(SortField.rating, description="Field to sort by"),
    sort_order: SortOrder = Query(SortOrder.desc, description="Sort order (asc or desc)"),
    skip: int = Query(0, ge=0, description="Number of shops to skip (pagination)"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of shops to return"),
):
    """List all shops with optional filtering, search, sorting, and pagination (all users)."""
    try:
        query = select(Shop)

        # Apply featured filter if provided
        if featured is not None:
            query = query.where(Shop.is_featured == featured)
            shops = session.exec(query).all()
            return shops
        
        # Apply category filter if provided
        if category_id is not None:
            query = query.where(Shop.category_id == category_id)
        
        # Apply search if provided
        if search:
            search_term = f"%{search}%"
            query = query.where(
                or_(
                    Shop.name.ilike(search_term),
                    Shop.description.ilike(search_term),
                    Shop.location_str.ilike(search_term)
                )
            )
        
        # Apply sorting: check if both parameters are at their default values
        is_default_sort = (
            sort_by == SortField.rating and 
            sort_order == SortOrder.desc
        )
        
        # If both are default, apply random ordering
        if is_default_sort:
            from sqlalchemy.sql.functions import random
            query = query.order_by(random())
        # Otherwise, apply the specified or default non-random sorting
        else:
            sort_column = getattr(Shop, sort_by.value)
            if sort_order == SortOrder.desc:
                query = query.order_by(desc(sort_column))
            else:
                query = query.order_by(asc(sort_column))
        
        
        # Apply pagination
        query = query.offset(skip).limit(limit)
        shops = session.exec(query).all()
        return shops
    finally:
        session.close()

@router.get("/{shop_id}", response_model=ShopRead)
async def get_shop(
    shop_id: int,
    session: Session = Depends(get_session),
    # current_user: User = Depends(get_current_user)
):
    """Get a shop by ID (all users)."""
    try:
        shop = session.exec(select(Shop).where(Shop.id == shop_id)).first()
        if not shop:
            raise HTTPException(status_code=404, detail="Shop not found")
        return shop
    finally:
        session.close()

@router.put("/{shop_id}", response_model=ShopRead)
async def update_shop(
    shop_id: int,
    shop_data: ShopUpdate = Depends(ShopUpdate.as_form),
    images: List[UploadFile] = File(default=[]),
    current_user: User = Depends(get_admin_user),
    session: Session = Depends(get_session)
):
    """Update a shop with images (admin only)."""
    try:
        shop = session.exec(select(Shop).where(Shop.id == shop_id)).first()
        if not shop:
            raise HTTPException(status_code=404, detail="Shop not found")
        
        # Update basic fields
        update_data = shop_data.model_dump(exclude_unset=True)
        
        # Validate category if being updated
        if "category_id" in update_data:
            category = session.exec(select(Category).where(Category.id == update_data["category_id"])).first()
            if not category:
                raise HTTPException(status_code=404, detail="Category not found")
        
        # Update fields
        for key, value in update_data.items():
            setattr(shop, key, value)
        
        if images:
            valid_images = []
            for image in images:
                if (image and 
                    hasattr(image, 'filename') and 
                    image.filename and 
                    image.filename.strip() and
                    image.size > 0):
                    valid_images.append(image)
            
            if valid_images:  # Only process if we have valid images
                # Delete old images
                if shop.image_urls:
                    old_images = shop.image_urls
                    await image_service.delete_images(old_images)
                
                # Save new images
                image_paths = []
                for image in valid_images:
                    image_path = image_service.get_image_url(
                        await image_service.save_image(image, "shops")
                    )
                    if image_path:
                        image_paths.append(image_path)
                shop.image_urls = image_paths
            else:
                # No valid images provided, clear existing images
                if shop.image_urls:
                    old_images = shop.image_urls
                    await image_service.delete_images(old_images)
                shop.image_urls = []
        shop.updated_at = datetime.utcnow()
        session.add(shop)
        session.commit()
        session.refresh(shop)
        return shop
    finally:
        session.close()

@router.delete("/{shop_id}")
async def delete_shop(
    shop_id: int,
    current_user: User = Depends(get_admin_user),
    session: Session = Depends(get_session)
):
    """Delete a shop (admin only)."""
    try:
        shop = session.exec(select(Shop).where(Shop.id == shop_id)).first()
        if not shop:
            raise HTTPException(status_code=404, detail="Shop not found")
        
        # Delete shop images
        if shop.image_urls:
            old_images = shop.image_urls
            await image_service.delete_images(old_images)
        
        session.delete(shop)
        session.commit()
        return {"message": "Shop deleted"}
    finally:
        session.close()

@router.patch("/{shop_id}/feature", response_model=ShopRead)
async def toggle_shop_featured(
    shop_id: int,
    is_featured: bool,
    current_user: User = Depends(get_admin_user),
    session: Session = Depends(get_session)
):
    """Toggle a shop's featured status (admin only)."""
    try:
        shop = session.exec(select(Shop).where(Shop.id == shop_id)).first()
        if not shop:
            raise HTTPException(status_code=404, detail="Shop not found")
        
        shop.is_featured = is_featured
        shop.updated_at = datetime.utcnow()
        
        session.add(shop)
        session.commit()
        session.refresh(shop)
        return shop
    finally:
        session.close()
