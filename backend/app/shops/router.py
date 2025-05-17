from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.db.session import get_session
from app.models.shop import Shop
from app.schemas.shop import ShopCreate, ShopRead
from app.auth.dependencies import get_admin_user
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