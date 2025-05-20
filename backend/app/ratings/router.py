from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from sqlalchemy import func
from app.db.session import get_session
from app.models.rating import Rating
from app.schemas.rating import RatingCreate, RatingRead, RatingUpdate
from app.auth.dependencies import get_current_user
from app.models.user import User
from app.models.shop import Shop
from datetime import datetime

router = APIRouter(prefix="/ratings", tags=["ratings"])

@router.post("/", response_model=RatingRead, status_code=status.HTTP_201_CREATED)
def create_rating(
    rating: RatingCreate,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    # Check if the user has already rated this shop
    existing_rating = session.exec(
        select(Rating).where(Rating.user_id == user.id, Rating.shop_id == rating.shop_id)
    ).first()
    if existing_rating:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have already rated this shop. Use PATCH to update your rating."
        )

    # Create new rating
    db_rating = Rating(
        user_id=user.id,
        shop_id=rating.shop_id,
        rating=rating.rating,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    # Update the shop's average rating
    shop = session.get(Shop, rating.shop_id)
    if shop:
        shop.rating = session.exec(
            select(func.avg(Rating.rating)).where(Rating.shop_id == shop.id)
        ).first() or 0
        shop.rating_count += 1
        session.add(shop)
            
    
    session.add(db_rating)
    session.commit()
    session.refresh(db_rating)
    return db_rating

@router.get("/{rating_id}", response_model=RatingRead)
def read_rating(
    rating_id: int,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    rating = session.get(Rating, rating_id)
    if not rating:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rating not found"
        )
    return rating

@router.get("/shop/{shop_id}", response_model=list[RatingRead])
def read_ratings_by_shop(
    shop_id: int,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    ratings = session.exec(select(Rating).where(Rating.shop_id == shop_id)).all()
    return ratings

@router.patch("/{rating_id}", response_model=RatingRead)
def update_rating(
    rating_id: int,
    rating_update: RatingUpdate,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    rating = session.get(Rating, rating_id)
    if not rating:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rating not found"
        )
    if rating.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own ratings"
        )

    rating_data = rating_update.dict(exclude_unset=True)
    for key, value in rating_data.items():
        setattr(rating, key, value)
    
    shop = session.get(Shop, rating.shop_id)
    if shop:
        shop.rating = session.exec(
            select(func.avg(Rating.rating)).where(Rating.shop_id == shop.id)
        ).first() or 0
        session.add(shop)
        
    rating.updated_at = datetime.utcnow()
    session.add(rating)
    session.commit()
    session.refresh(rating)
    return rating

@router.delete("/{rating_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_rating(
    rating_id: int,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    rating = session.get(Rating, rating_id)
    if not rating:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rating not found"
        )
    if rating.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own ratings"
        )
    
    shop = session.get(Shop, rating.shop_id)
    if shop:
        session.delete(rating)
        session.commit()  # Commit the deletion first
        
        # Now calculate new average with the rating removed
        shop.rating = session.exec(
            select(func.avg(Rating.rating)).where(Rating.shop_id == shop.id)
        ).first() or 0
        shop.rating_count -= 1
        session.add(shop)
        session.commit()
        return None