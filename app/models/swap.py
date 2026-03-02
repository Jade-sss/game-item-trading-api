import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    String,
    Table,
    Text,
)
from sqlalchemy.orm import relationship

from app.database import Base

# Association tables for many-to-many between swaps and items
swap_offered_items = Table(
    "swap_offered_items",
    Base.metadata,
    Column("swap_id", String, ForeignKey("swaps.id"), primary_key=True),
    Column("item_id", String, ForeignKey("items.id"), primary_key=True),
)

swap_requested_items = Table(
    "swap_requested_items",
    Base.metadata,
    Column("swap_id", String, ForeignKey("swaps.id"), primary_key=True),
    Column("item_id", String, ForeignKey("items.id"), primary_key=True),
)


class Swap(Base):
    __tablename__ = "swaps"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    proposer_id = Column(String, ForeignKey("users.id"), nullable=False)
    receiver_id = Column(String, ForeignKey("users.id"), nullable=False)
    status = Column(
        String(20), default="pending", nullable=False, index=True
    )  # pending, accepted, rejected, cancelled, completed
    message = Column(Text, nullable=True)

    # Rating fields (after swap is completed)
    proposer_rating = Column(Float, nullable=True)  # Rating given BY proposer TO receiver
    proposer_review = Column(Text, nullable=True)
    receiver_rating = Column(Float, nullable=True)  # Rating given BY receiver TO proposer
    receiver_review = Column(Text, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    proposer = relationship("User", foreign_keys=[proposer_id], back_populates="proposed_swaps")
    receiver = relationship("User", foreign_keys=[receiver_id], back_populates="received_swaps")
    offered_items = relationship("Item", secondary=swap_offered_items)
    requested_items = relationship("Item", secondary=swap_requested_items)
