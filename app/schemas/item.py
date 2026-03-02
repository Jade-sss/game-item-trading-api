from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class ItemRarity(str, Enum):
    common = "common"
    uncommon = "uncommon"
    rare = "rare"
    epic = "epic"
    legendary = "legendary"


class ItemCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    game: str = Field(..., min_length=1, max_length=100)
    category: Optional[str] = Field(None, max_length=100)
    rarity: Optional[ItemRarity] = None
    image_url: Optional[str] = Field(None, max_length=500)
    estimated_value: Optional[float] = Field(None, ge=0)


class ItemUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    game: Optional[str] = Field(None, min_length=1, max_length=100)
    category: Optional[str] = Field(None, max_length=100)
    rarity: Optional[ItemRarity] = None
    image_url: Optional[str] = Field(None, max_length=500)
    estimated_value: Optional[float] = Field(None, ge=0)
    is_available: Optional[bool] = None


class ItemResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    game: str
    category: Optional[str]
    rarity: Optional[str]
    image_url: Optional[str]
    estimated_value: Optional[float]
    is_available: bool
    owner_id: str
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class ItemWithOwnerResponse(ItemResponse):
    owner_username: Optional[str] = None
