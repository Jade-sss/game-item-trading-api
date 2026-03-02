from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field

from app.schemas.item import ItemResponse


class SwapStatus(str, Enum):
    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"
    cancelled = "cancelled"
    completed = "completed"


class SwapCreate(BaseModel):
    receiver_id: str
    offered_item_ids: List[str] = Field(..., min_length=1)
    requested_item_ids: List[str] = Field(..., min_length=1)
    message: Optional[str] = Field(None, max_length=1000)


class SwapRate(BaseModel):
    rating: float = Field(..., ge=1, le=5)
    review: Optional[str] = Field(None, max_length=1000)


class SwapResponse(BaseModel):
    id: str
    proposer_id: str
    receiver_id: str
    status: str
    message: Optional[str]
    proposer_rating: Optional[float]
    proposer_review: Optional[str]
    receiver_rating: Optional[float]
    receiver_review: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class SwapDetailResponse(SwapResponse):
    offered_items: List[ItemResponse] = []
    requested_items: List[ItemResponse] = []
    proposer_username: Optional[str] = None
    receiver_username: Optional[str] = None
