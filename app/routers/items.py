from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.item import Item
from app.models.user import User
from app.schemas.item import ItemCreate, ItemResponse, ItemUpdate, ItemWithOwnerResponse

router = APIRouter(prefix="/api/items", tags=["Items"])


@router.post("/", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
def create_item(
    payload: ItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add a new item to the authenticated user's inventory."""
    item = Item(
        **payload.model_dump(),
        owner_id=current_user.id,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.get("/", response_model=List[ItemWithOwnerResponse])
def list_items(
    game: Optional[str] = Query(None, description="Filter by game name"),
    category: Optional[str] = Query(None, description="Filter by category"),
    rarity: Optional[str] = Query(None, description="Filter by rarity"),
    search: Optional[str] = Query(None, description="Search items by name"),
    available_only: bool = Query(True, description="Only show available items"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """List and search items with optional filters."""
    query = db.query(Item)

    if available_only:
        query = query.filter(Item.is_available == True)
    if game:
        query = query.filter(Item.game.ilike(f"%{game}%"))
    if category:
        query = query.filter(Item.category.ilike(f"%{category}%"))
    if rarity:
        query = query.filter(Item.rarity == rarity)
    if search:
        query = query.filter(Item.name.ilike(f"%{search}%"))

    items = query.order_by(Item.created_at.desc()).offset(skip).limit(limit).all()

    # Enrich with owner username
    result = []
    for item in items:
        item_dict = ItemWithOwnerResponse.model_validate(item).model_dump()
        owner = db.query(User).filter(User.id == item.owner_id).first()
        item_dict["owner_username"] = owner.username if owner else None
        result.append(item_dict)

    return result


@router.get("/my", response_model=List[ItemResponse])
def list_my_items(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
):
    """List all items owned by the authenticated user."""
    items = (
        db.query(Item)
        .filter(Item.owner_id == current_user.id)
        .order_by(Item.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return items


@router.get("/{item_id}", response_model=ItemWithOwnerResponse)
def get_item(item_id: str, db: Session = Depends(get_db)):
    """View details of a specific item."""
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found",
        )

    result = ItemWithOwnerResponse.model_validate(item).model_dump()
    owner = db.query(User).filter(User.id == item.owner_id).first()
    result["owner_username"] = owner.username if owner else None
    return result


@router.put("/{item_id}", response_model=ItemResponse)
def update_item(
    item_id: str,
    payload: ItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update an item (only the owner can update)."""
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found",
        )
    if item.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own items",
        )

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(item, field, value)

    db.commit()
    db.refresh(item)
    return item


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(
    item_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete an item (only the owner can delete)."""
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found",
        )
    if item.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own items",
        )

    db.delete(item)
    db.commit()
