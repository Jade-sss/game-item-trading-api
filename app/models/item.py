import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Enum, Float, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class ItemRarity(str):
    COMMON = "common"
    UNCOMMON = "uncommon"
    RARE = "rare"
    EPIC = "epic"
    LEGENDARY = "legendary"


class Item(Base):
    __tablename__ = "items"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)
    game = Column(String(100), nullable=False, index=True)
    category = Column(String(100), nullable=True, index=True)
    rarity = Column(String(20), nullable=True)
    image_url = Column(String(500), nullable=True)
    estimated_value = Column(Float, nullable=True)
    is_available = Column(Boolean, default=True)
    owner_id = Column(String, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    owner = relationship("User", back_populates="items")
