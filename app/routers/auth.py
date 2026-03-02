from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.postal_code import PostalCode
from app.models.user import User
from app.schemas.user import Token, UserLogin, UserRegister, UserResponse
from app.utils.security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(payload: UserRegister, db: Session = Depends(get_db)):
    """Register a new user account.

    Collects: email, password, first name, last name, nickname,
    phone number (optional), and postal code (validated against
    the postal_codes table which auto-fills city, state, lat/lon).
    """
    # Check duplicate email
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    # Validate postal code against lookup table
    pc_record = (
        db.query(PostalCode)
        .filter(PostalCode.postal_code == payload.postal_code)
        .first()
    )
    if not pc_record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid postal code '{payload.postal_code}'. Use GET /api/postal-codes to find valid codes.",
        )

    # Generate a unique username from the email local part
    base_username = payload.email.split("@")[0].lower()
    username = base_username
    counter = 1
    while db.query(User).filter(User.username == username).first():
        username = f"{base_username}{counter}"
        counter += 1

    user = User(
        username=username,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        first_name=payload.first_name,
        last_name=payload.last_name,
        nickname=payload.nickname,
        phone_number=payload.phone_number,
        postal_code=pc_record.postal_code,
        city=pc_record.city,
        state=pc_record.state,
        latitude=pc_record.latitude,
        longitude=pc_record.longitude,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=Token)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    """Authenticate user and return a JWT access token."""
    user = db.query(User).filter(User.email == payload.email).first()

    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )

    access_token = create_access_token(data={"sub": user.id})
    return Token(access_token=access_token)
