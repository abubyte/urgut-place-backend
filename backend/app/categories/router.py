from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List

from app.db.session import get_session
from app.models.category import Category
from app.schemas.category import CategoryCreate, CategoryRead, CategoryUpdate
from app.auth.dependencies import get_admin_user, get_current_user
from app.models.user import User

router = APIRouter(prefix="/categories", tags=["categories"])

@router.post("", response_model=CategoryRead)
async def create_category(
    category_data: CategoryCreate = Depends(CategoryCreate.as_form),
    current_user: User = Depends(get_admin_user),
    session: Session = Depends(get_session)
):
    """Create a new category (admin only)."""
    category = Category(**category_data.model_dump())
    session.add(category)
    session.commit()
    session.refresh(category)
    return category

@router.get("", response_model=List[CategoryRead])
async def list_categories(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """List all categories (all users)."""
    categories = session.exec(select(Category)).all()
    return categories

@router.get("/{category_id}", response_model=CategoryRead)
async def get_category(
    category_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Get a category by ID (all users)."""
    category = session.exec(select(Category).where(Category.id == category_id)).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category

@router.put("/{category_id}", response_model=CategoryRead)
async def update_category(
    category_id: int,
    category_data: CategoryUpdate = Depends(CategoryUpdate.as_form),
    current_user: User = Depends(get_admin_user),
    session: Session = Depends(get_session)
):
    """Update a category (admin only)."""
    category = session.exec(select(Category).where(Category.id == category_id)).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    update_data = category_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(category, key, value)
    session.add(category)
    session.commit()
    session.refresh(category)
    return category

@router.delete("/{category_id}")
async def delete_category(
    category_id: int,
    current_user: User = Depends(get_admin_user),
    session: Session = Depends(get_session)
):
    """Delete a category (admin only)."""
    category = session.exec(select(Category).where(Category.id == category_id)).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    session.delete(category)
    session.commit()
    return {"message": "Category deleted"}