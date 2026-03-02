from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.item import Item
from app.models.swap import Swap
from app.models.user import User
from app.schemas.item import ItemResponse
from app.schemas.swap import SwapCreate, SwapDetailResponse, SwapRate, SwapResponse

router = APIRouter(prefix="/api/swaps", tags=["Swaps"])


def _build_swap_detail(swap: Swap, db: Session) -> dict:
    """Build a SwapDetailResponse dict from a Swap ORM instance."""
    data = SwapDetailResponse.model_validate(swap).model_dump()
    data["offered_items"] = [
        ItemResponse.model_validate(i).model_dump() for i in swap.offered_items
    ]
    data["requested_items"] = [
        ItemResponse.model_validate(i).model_dump() for i in swap.requested_items
    ]
    proposer = db.query(User).filter(User.id == swap.proposer_id).first()
    receiver = db.query(User).filter(User.id == swap.receiver_id).first()
    data["proposer_username"] = proposer.username if proposer else None
    data["receiver_username"] = receiver.username if receiver else None
    return data


# ─── Propose a swap ──────────────────────────────────────────────────────────

@router.post("/", response_model=SwapDetailResponse, status_code=status.HTTP_201_CREATED)
def propose_swap(
    payload: SwapCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Propose a new item swap to another user."""
    if payload.receiver_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot propose a swap with yourself",
        )

    receiver = db.query(User).filter(User.id == payload.receiver_id).first()
    if not receiver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Receiver user not found",
        )

    # Validate offered items belong to current user and are available
    offered_items = (
        db.query(Item)
        .filter(Item.id.in_(payload.offered_item_ids), Item.owner_id == current_user.id)
        .all()
    )
    if len(offered_items) != len(payload.offered_item_ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Some offered items are not found or don't belong to you",
        )
    for item in offered_items:
        if not item.is_available:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Item '{item.name}' is not available for trading",
            )

    # Validate requested items belong to receiver and are available
    requested_items = (
        db.query(Item)
        .filter(Item.id.in_(payload.requested_item_ids), Item.owner_id == payload.receiver_id)
        .all()
    )
    if len(requested_items) != len(payload.requested_item_ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Some requested items are not found or don't belong to the receiver",
        )
    for item in requested_items:
        if not item.is_available:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Item '{item.name}' is not available for trading",
            )

    swap = Swap(
        proposer_id=current_user.id,
        receiver_id=payload.receiver_id,
        message=payload.message,
    )
    swap.offered_items = offered_items
    swap.requested_items = requested_items

    db.add(swap)
    db.commit()
    db.refresh(swap)

    return _build_swap_detail(swap, db)


# ─── Accept a swap ───────────────────────────────────────────────────────────

@router.post("/{swap_id}/accept", response_model=SwapDetailResponse)
def accept_swap(
    swap_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Accept a pending swap (only the receiver can accept)."""
    swap = db.query(Swap).filter(Swap.id == swap_id).first()
    if not swap:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Swap not found")

    if swap.receiver_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the receiver can accept this swap",
        )

    if swap.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Swap is already '{swap.status}', cannot accept",
        )

    # Transfer ownership of items
    for item in swap.offered_items:
        item.owner_id = swap.receiver_id
    for item in swap.requested_items:
        item.owner_id = swap.proposer_id

    swap.status = "completed"
    swap.completed_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(swap)
    return _build_swap_detail(swap, db)


# ─── Reject a swap ───────────────────────────────────────────────────────────

@router.post("/{swap_id}/reject", response_model=SwapDetailResponse)
def reject_swap(
    swap_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Reject a pending swap (only the receiver can reject)."""
    swap = db.query(Swap).filter(Swap.id == swap_id).first()
    if not swap:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Swap not found")

    if swap.receiver_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the receiver can reject this swap",
        )

    if swap.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Swap is already '{swap.status}', cannot reject",
        )

    swap.status = "rejected"
    db.commit()
    db.refresh(swap)
    return _build_swap_detail(swap, db)


# ─── Cancel a swap ───────────────────────────────────────────────────────────

@router.post("/{swap_id}/cancel", response_model=SwapDetailResponse)
def cancel_swap(
    swap_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Cancel a pending swap (only the proposer can cancel)."""
    swap = db.query(Swap).filter(Swap.id == swap_id).first()
    if not swap:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Swap not found")

    if swap.proposer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the proposer can cancel this swap",
        )

    if swap.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Swap is already '{swap.status}', cannot cancel",
        )

    swap.status = "cancelled"
    db.commit()
    db.refresh(swap)
    return _build_swap_detail(swap, db)


# ─── Rate a completed swap ───────────────────────────────────────────────────

@router.post("/{swap_id}/rate", response_model=SwapDetailResponse)
def rate_swap(
    swap_id: str,
    payload: SwapRate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Rate a completed swap. Each party can rate the other once."""
    swap = db.query(Swap).filter(Swap.id == swap_id).first()
    if not swap:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Swap not found")

    if swap.status != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only rate completed swaps",
        )

    if current_user.id == swap.proposer_id:
        if swap.proposer_rating is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You have already rated this swap",
            )
        swap.proposer_rating = payload.rating
        swap.proposer_review = payload.review

        # Update receiver's rating
        receiver = db.query(User).filter(User.id == swap.receiver_id).first()
        receiver.total_ratings += payload.rating
        receiver.rating_count += 1

    elif current_user.id == swap.receiver_id:
        if swap.receiver_rating is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You have already rated this swap",
            )
        swap.receiver_rating = payload.rating
        swap.receiver_review = payload.review

        # Update proposer's rating
        proposer = db.query(User).filter(User.id == swap.proposer_id).first()
        proposer.total_ratings += payload.rating
        proposer.rating_count += 1

    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a participant in this swap",
        )

    db.commit()
    db.refresh(swap)
    return _build_swap_detail(swap, db)


# ─── Swap history ────────────────────────────────────────────────────────────

@router.get("/history", response_model=List[SwapResponse])
def swap_history(
    swap_status: Optional[str] = Query(None, alias="status", description="Filter by status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get the authenticated user's swap history."""
    query = db.query(Swap).filter(
        (Swap.proposer_id == current_user.id) | (Swap.receiver_id == current_user.id)
    )

    if swap_status:
        query = query.filter(Swap.status == swap_status)

    swaps = query.order_by(Swap.created_at.desc()).offset(skip).limit(limit).all()
    return swaps


# ─── Swap detail ─────────────────────────────────────────────────────────────

@router.get("/{swap_id}", response_model=SwapDetailResponse)
def get_swap_detail(
    swap_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get full details of a specific swap (participants only)."""
    swap = db.query(Swap).filter(Swap.id == swap_id).first()
    if not swap:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Swap not found")

    if current_user.id not in (swap.proposer_id, swap.receiver_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a participant in this swap",
        )

    return _build_swap_detail(swap, db)
