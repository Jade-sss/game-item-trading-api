from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.postal_code import PostalCode
from app.models.user import User
from app.schemas.user import (
    PasswordChange,
    UserPublicResponse,
    UserResponse,
    UserUpdate,
)
from app.utils.security import hash_password, verify_password

router = APIRouter(prefix="/api/users", tags=["Users"])


@router.get("/me", response_model=UserResponse)
def get_my_profile(current_user: User = Depends(get_current_user)):
    """Get the authenticated user's full profile (main menu info)."""
    return current_user


@router.put("/me", response_model=UserResponse)
def update_my_profile(
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update the authenticated user's profile information."""
    update_data = payload.model_dump(exclude_unset=True)

    if "email" in update_data and update_data["email"] != current_user.email:
        existing = db.query(User).filter(User.email == update_data["email"]).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already in use by another account",
            )

    # If postal_code is being changed, validate and auto-fill city/state/lat/lon
    if "postal_code" in update_data and update_data["postal_code"] is not None:
        pc_record = (
            db.query(PostalCode)
            .filter(PostalCode.postal_code == update_data["postal_code"])
            .first()
        )
        if not pc_record:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid postal code '{update_data['postal_code']}'. "
                       f"Use GET /api/postal-codes to find valid codes.",
            )
        update_data["city"] = pc_record.city
        update_data["state"] = pc_record.state
        update_data["latitude"] = pc_record.latitude
        update_data["longitude"] = pc_record.longitude

    for field, value in update_data.items():
        setattr(current_user, field, value)

    db.commit()
    db.refresh(current_user)
    return current_user


@router.put("/me/password", status_code=status.HTTP_200_OK)
def change_password(
    payload: PasswordChange,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Change the authenticated user's password."""
    if not verify_password(payload.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    current_user.hashed_password = hash_password(payload.new_password)
    db.commit()
    return {"message": "Password updated successfully"}


@router.get("/{user_id}", response_model=UserPublicResponse)
def get_user_profile(user_id: str, db: Session = Depends(get_db)):
    """Get a user's public profile by ID."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user
