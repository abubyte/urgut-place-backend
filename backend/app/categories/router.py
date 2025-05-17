from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.db.session import get_session
from app.models.category import Category
from app.schemas.category import CategoryCreate, CategoryRead
from app.auth.dependencies import get_admin_user
from app.models.user import User

router = APIRouter(prefix="/categories", tags=["categories"])

@router.post("", response_model=CategoryRead)
async def create_category(
    category_data: CategoryCreate,
    current_user: User = Depends(get_admin_user),
    session: Session = Depends(get_session)
):
    """Create a new category (admin only)."""
    category = Category(**category_data.model_dump())
    session.add(category)
    session.commit()
    session.refresh(category)
    return category