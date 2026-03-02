import uuid

from sqlalchemy import Column, Float, String
from sqlalchemy.orm import Session

from app.database import Base


class PostalCode(Base):
    __tablename__ = "postal_codes"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    postal_code = Column(String(20), unique=True, nullable=False, index=True)
    city = Column(String(100), nullable=False, index=True)
    state = Column(String(50), nullable=False, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)


def load_postal_codes(db: Session, data: list) -> int:
    """
    Bulk-insert postal code records.

    Parameters
    ----------
    db : Session
    data : list of tuples  – (postal_code, city, state, latitude, longitude)

    Returns
    -------
    int – number of rows inserted
    """
    if not data:
        return 0

    records = [
        PostalCode(
            postal_code=pc, city=city, state=state, latitude=lat, longitude=lon
        )
        for pc, city, state, lat, lon in data
    ]
    db.add_all(records)
    db.commit()
    return len(records)
