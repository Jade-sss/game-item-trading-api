import csv
import os
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import Base, SessionLocal, engine
from app.models.postal_code import PostalCode, load_postal_codes
from app.routers import auth, items, postal_codes, swaps, users

# Import all models so Base.metadata knows about them
import app.models.postal_code  # noqa: F401

# Create all tables
Base.metadata.create_all(bind=engine)

# --- Auto-seed postal codes from CSV on first run ---
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
CSV_PATH = DATA_DIR / "postal_codes.csv"


def _seed_postal_codes_from_csv() -> None:
    """Load postal codes from data/postal_codes.csv if the table is empty."""
    if not CSV_PATH.exists():
        return

    db = SessionLocal()
    try:
        if db.query(PostalCode).first() is not None:
            return  # already seeded

        rows = []
        with open(CSV_PATH, newline="", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            for i, row in enumerate(reader):
                if len(row) < 5:
                    continue
                # Skip header row
                if i == 0 and row[0].strip().lower() in (
                    "postal_code", "zip", "zipcode", "zip_code", "postalcode",
                ):
                    continue
                try:
                    rows.append((
                        row[0].strip(),
                        row[1].strip(),
                        row[2].strip(),
                        float(row[3].strip()),
                        float(row[4].strip()),
                    ))
                except (ValueError, IndexError):
                    continue

        if rows:
            count = load_postal_codes(db, rows)
            print(f"[startup] Loaded {count} postal codes from {CSV_PATH}")
    finally:
        db.close()


_seed_postal_codes_from_csv()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="REST API for trading in-game items between users",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(items.router)
app.include_router(swaps.router)
app.include_router(postal_codes.router)

# Serve static files (CSS, JS)
STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/", tags=["Health"])
def root():
    return FileResponse(str(STATIC_DIR / "index.html"))


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "healthy"}


# SPA catch-all: serve index.html for any non-API, non-static path
@app.get("/{full_path:path}", include_in_schema=False)
async def spa_catch_all(request: Request, full_path: str):
    # Don't catch API or static routes
    if full_path.startswith("api/") or full_path.startswith("static/") or full_path in ("docs", "redoc", "openapi.json", "health"):
        return  # will 404 naturally
    return FileResponse(str(STATIC_DIR / "index.html"))
