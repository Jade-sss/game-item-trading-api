from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


# --- Auth schemas ---
class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=128)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    nickname: str = Field(..., min_length=1, max_length=100, description="Display name")
    phone_number: Optional[str] = Field(None, max_length=20, pattern=r"^\+?[\d\s\-().]{7,20}$")
    postal_code: str = Field(..., min_length=3, max_length=20)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: Optional[str] = None


# --- User schemas ---
class UserUpdate(BaseModel):
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    nickname: Optional[str] = Field(None, min_length=1, max_length=100)
    phone_number: Optional[str] = Field(None, max_length=20, pattern=r"^\+?[\d\s\-().]{7,20}$")
    postal_code: Optional[str] = Field(None, min_length=3, max_length=20)
    bio: Optional[str] = Field(None, max_length=500)
    avatar_url: Optional[str] = Field(None, max_length=500)
    email: Optional[EmailStr] = None


class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    first_name: str
    last_name: str
    nickname: str
    phone_number: Optional[str]
    city: Optional[str]
    state: Optional[str]
    postal_code: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    bio: Optional[str]
    avatar_url: Optional[str]
    is_active: bool
    average_rating: float
    rating_count: float
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class UserPublicResponse(BaseModel):
    id: str
    username: str
    nickname: str
    city: Optional[str]
    state: Optional[str]
    bio: Optional[str]
    avatar_url: Optional[str]
    average_rating: float
    rating_count: float
    created_at: datetime

    class Config:
        from_attributes = True


class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=6, max_length=128)


# --- Postal code schemas ---
class PostalCodeResponse(BaseModel):
    postal_code: str
    city: str
    state: str
    latitude: float
    longitude: float

    class Config:
        from_attributes = True
