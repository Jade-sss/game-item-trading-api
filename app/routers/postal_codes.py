from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.postal_code import PostalCode, load_postal_codes
from app.schemas.user import PostalCodeResponse

router = APIRouter(prefix="/api/postal-codes", tags=["Postal Codes"])


@router.get("/", response_model=List[PostalCodeResponse])
def list_postal_codes(
    city: Optional[str] = Query(None, description="Filter by city name"),
    state: Optional[str] = Query(None, description="Filter by state abbreviation"),
    search: Optional[str] = Query(None, description="Search by postal code prefix, city, or state"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """List postal codes with optional city/state/search filters."""
    query = db.query(PostalCode)

    if city:
        query = query.filter(PostalCode.city.ilike(f"%{city}%"))
    if state:
        query = query.filter(PostalCode.state.ilike(f"{state}"))
    if search:
        query = query.filter(
            (PostalCode.postal_code.ilike(f"{search}%"))
            | (PostalCode.city.ilike(f"%{search}%"))
            | (PostalCode.state.ilike(f"{search}%"))
        )

    results = (
        query.order_by(PostalCode.state, PostalCode.city, PostalCode.postal_code)
        .offset(skip)
        .limit(limit)
        .all()
    )
    return results


@router.get("/{postal_code}", response_model=PostalCodeResponse)
def get_postal_code(postal_code: str, db: Session = Depends(get_db)):
    """Look up a specific postal code to get its city, state, and coordinates."""
    record = db.query(PostalCode).filter(PostalCode.postal_code == postal_code).first()
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Postal code '{postal_code}' not found",
        )
    return record


@router.post("/bulk-load", status_code=status.HTTP_201_CREATED)
def bulk_load_postal_codes(
    file: UploadFile = File(..., description="CSV file: postal_code,city,state,latitude,longitude"),
    db: Session = Depends(get_db),
):
    """
    Bulk-load postal codes from a CSV file.

    Expected CSV format (with or without header row):
        postal_code,city,state,latitude,longitude
        10001,New York,NY,40.7484,-73.9967
    """
    import csv
    import io

    content = file.file.read().decode("utf-8")
    reader = csv.reader(io.StringIO(content))

    rows = []
    for i, row in enumerate(reader):
        if len(row) < 5:
            continue
        # Skip header row if present
        if i == 0 and row[0].strip().lower() in ("postal_code", "zip", "zipcode", "zip_code"):
            continue
        pc, city, state, lat, lon = (
            row[0].strip(),
            row[1].strip(),
            row[2].strip(),
            row[3].strip(),
            row[4].strip(),
        )
        # Skip if this postal code already exists
        existing = db.query(PostalCode).filter(PostalCode.postal_code == pc).first()
        if existing:
            continue
        try:
            rows.append((pc, city, state, float(lat), float(lon)))
        except ValueError:
            continue  # skip rows with bad numeric data

    count = load_postal_codes(db, rows)
    return {"message": f"Loaded {count} postal codes", "count": count}
