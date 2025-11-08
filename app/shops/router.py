from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from pydantic import BeforeValidator
from sqlmodel import Session, select, or_, desc, asc
from sqlalchemy import cast, String
from typing import Annotated, Any, List, Optional, Union
from datetime import datetime
from enum import Enum
from pydantic.json_schema import SkipJsonSchema
from dateutil.relativedelta import relativedelta

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

def auto_deactivate_expired_shops(session: Session):
    """Automatically deactivate shops that have expired."""
    try:
        expired_shops = session.exec(
            select(Shop).where(
                Shop.is_active == True,
                Shop.expires_at != None,
                Shop.expires_at <= datetime.utcnow()
            )
        ).all()
        
        for shop in expired_shops:
            shop.is_active = False
            session.add(shop)
        
        if expired_shops:
            session.commit()
    except Exception as e:
        session.rollback()
        raise e

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
        
        # Create shop - handle JSON fields separately
        shop_dict = shop_data.model_dump(exclude={'seller_phones', 'social_networks'})
        
        # Calculate expiration date
        expires_at = datetime.utcnow() + relativedelta(months=shop_dict['expiration_months'])
        shop_dict['expires_at'] = expires_at
        
        shop = Shop(**shop_dict)
        # Set JSON fields using properties
        shop.seller_phones = shop_data.seller_phones
        shop.social_networks = shop_data.social_networks
        
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
        
        return ShopRead.from_shop(shop)
    finally:
        session.close()

@router.get("", response_model=List[ShopRead])
async def list_shops(
    session: Session = Depends(get_session),
    category_id: Optional[int] = Query(None, description="Filter by category ID"),
    search: Optional[str] = Query(None, description="Search in name, description, and location"),
    featured: Optional[bool] = Query(None, description="Filter by featured status"),
    is_active: Optional[bool] = Query(None, description="Filter by active status (None=only active, True=active, False=inactive)"),
    sort_by: SortField = Query(SortField.rating, description="Field to sort by"),
    sort_order: SortOrder = Query(SortOrder.desc, description="Sort order (asc or desc)"),
    skip: int = Query(0, ge=0, description="Number of shops to skip (pagination)"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of shops to return"),
):
    """List shops with filtering. By default, only shows active and non-expired shops."""
    try:
        # Auto-deactivate expired shops before listing
        auto_deactivate_expired_shops(session)
        
        query = select(Shop)

        # Default behavior: only show active shops
        if is_active is None:
            query = query.where(Shop.is_active == True)
        else:
            # If explicitly specified, filter by is_active
            query = query.where(Shop.is_active == is_active)

        # Apply featured filter if provided
        if featured is not None:
            query = query.where(Shop.is_featured == featured)
        
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
                    cast(Shop.sector, String).ilike(search_term),
                    cast(Shop.number, String).ilike(search_term)
                )
            )
        
        # Apply sorting
        is_default_sort = (
            sort_by == SortField.rating and 
            sort_order == SortOrder.desc
        )
        
        if is_default_sort:
            from sqlalchemy.sql.functions import random
            query = query.order_by(random())
        else:
            sort_column = getattr(Shop, sort_by.value)
            if sort_order == SortOrder.desc:
                query = query.order_by(desc(sort_column))
            else:
                query = query.order_by(asc(sort_column))
        
        # Apply pagination
        query = query.offset(skip).limit(limit)
        shops = session.exec(query).all()
        return [ShopRead.from_shop(shop) for shop in shops]
    finally:
        session.close()

@router.get("/{shop_id}", response_model=ShopRead)
async def get_shop(
    shop_id: int,
    session: Session = Depends(get_session),
):
    """Get a shop by ID (all users)."""
    try:
        # Auto-deactivate expired shops
        auto_deactivate_expired_shops(session)
        
        shop = session.exec(select(Shop).where(Shop.id == shop_id)).first()
        if not shop:
            raise HTTPException(status_code=404, detail="Shop not found")
        return ShopRead.from_shop(shop)
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
        
        # Update basic fields - handle JSON fields separately
        all_update_data = shop_data.model_dump(exclude_unset=True)
        update_data = {k: v for k, v in all_update_data.items() if k not in {'seller_phones', 'social_networks'}}
        
        # Validate category if being updated
        if "category_id" in update_data:
            category = session.exec(select(Category).where(Category.id == update_data["category_id"])).first()
            if not category:
                raise HTTPException(status_code=404, detail="Category not found")
        
        # Recalculate expiration if expiration_months changed
        if "expiration_months" in update_data:
            shop.expiration_months = update_data["expiration_months"]
            shop.expires_at = shop.created_at + relativedelta(months=shop.expiration_months)
        
        # Update fields
        for key, value in update_data.items():
            if key != "expiration_months":  # Already handled above
                setattr(shop, key, value)
        
        # Update JSON fields using properties
        if "seller_phones" in all_update_data:
            shop.seller_phones = all_update_data["seller_phones"]
        if "social_networks" in all_update_data:
            shop.social_networks = all_update_data["social_networks"]
        
        # Handle images
        if images:
            valid_images = []
            for image in images:
                if (image and 
                    hasattr(image, 'filename') and 
                    image.filename and 
                    image.filename.strip() and
                    image.size > 0):
                    valid_images.append(image)
            
            if valid_images:
                if shop.image_urls:
                    old_images = shop.image_urls
                    await image_service.delete_images(old_images)
                
                image_paths = []
                for image in valid_images:
                    image_path = image_service.get_image_url(
                        await image_service.save_image(image, "shops")
                    )
                    if image_path:
                        image_paths.append(image_path)
                shop.image_urls = image_paths
            else:
                if shop.image_urls:
                    old_images = shop.image_urls
                    await image_service.delete_images(old_images)
                shop.image_urls = []
                
        shop.updated_at = datetime.utcnow()
        session.add(shop)
        session.commit()
        session.refresh(shop)
        return ShopRead.from_shop(shop)
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
        return ShopRead.from_shop(shop)
    finally:
        session.close()

@router.patch("/{shop_id}/activate", response_model=ShopRead)
async def activate_shop(
    shop_id: int,
    months: int = Form(..., ge=1, le=120, description="Number of months to activate the shop for"),
    current_user: User = Depends(get_admin_user),
    session: Session = Depends(get_session)
):
    """
    Activate an expired/inactive shop for specified number of months (admin only).
    This will set is_active=True and calculate new expiration date from now.
    """
    try:
        shop = session.exec(select(Shop).where(Shop.id == shop_id)).first()
        if not shop:
            raise HTTPException(status_code=404, detail="Shop not found")
        
        # Activate the shop
        shop.is_active = True
        shop.expiration_months = months
        # Calculate new expiration from current time
        shop.expires_at = datetime.utcnow() + relativedelta(months=months)
        shop.updated_at = datetime.utcnow()
        
        session.add(shop)
        session.commit()
        session.refresh(shop)
        return ShopRead.from_shop(shop)
    finally:
        session.close()

@router.patch("/{shop_id}/deactivate", response_model=ShopRead)
async def deactivate_shop(
    shop_id: int,
    current_user: User = Depends(get_admin_user),
    session: Session = Depends(get_session)
):
    """
    Manually deactivate a shop (admin only).
    This will set is_active=False regardless of expiration date.
    """
    try:
        shop = session.exec(select(Shop).where(Shop.id == shop_id)).first()
        if not shop:
            raise HTTPException(status_code=404, detail="Shop not found")
        
        shop.is_active = False
        shop.updated_at = datetime.utcnow()
        
        session.add(shop)
        session.commit()
        session.refresh(shop)
        return ShopRead.from_shop(shop)
    finally:
        session.close()