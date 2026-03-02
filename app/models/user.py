import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Float, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(120), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    nickname = Column(String(100), nullable=False)  # display name
    phone_number = Column(String(20), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(50), nullable=True)
    postal_code = Column(String(20), nullable=True, index=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    bio = Column(Text, nullable=True)
    avatar_url = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True)
    rating = Column(Float, default=0.0)
    total_ratings = Column(Float, default=0)
    rating_count = Column(Float, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    items = relationship("Item", back_populates="owner", cascade="all, delete-orphan")
    proposed_swaps = relationship(
        "Swap",
        foreign_keys="Swap.proposer_id",
        back_populates="proposer",
    )
    received_swaps = relationship(
        "Swap",
        foreign_keys="Swap.receiver_id",
        back_populates="receiver",
    )

    @property
    def average_rating(self) -> float:
        if self.rating_count == 0:
            return 0.0
        return round(self.total_ratings / self.rating_count, 2)
