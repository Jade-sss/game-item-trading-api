"""
Shared pytest fixtures for the Game Item Trading API test suite.

Uses an in-memory SQLite database so tests are fast and isolated.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models.postal_code import PostalCode
from app.utils.security import create_access_token

# In-memory SQLite for tests
TEST_DATABASE_URL = "sqlite://"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ── DB session fixture ─────────────────────────────────────────
@pytest.fixture(autouse=True)
def db():
    """Create a fresh database for every single test."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


# ── Override the FastAPI dependency ────────────────────────────
@pytest.fixture(autouse=True)
def override_get_db(db):
    """Swap the real DB dependency for the test session."""
    def _get_test_db():
        try:
            yield db
        finally:
            pass  # session closed by the db fixture

    app.dependency_overrides[get_db] = _get_test_db
    yield
    app.dependency_overrides.clear()


# ── Test HTTP client ───────────────────────────────────────────
@pytest.fixture
def client():
    return TestClient(app)


# ── Seed a valid postal code ──────────────────────────────────
@pytest.fixture
def seed_postal_code(db):
    """Insert a postal code row so registration / updates don't fail validation."""
    pc = PostalCode(
        postal_code="10001",
        city="New York",
        state="NY",
        latitude=40.7484,
        longitude=-73.9967,
    )
    db.add(pc)
    pc2 = PostalCode(
        postal_code="90210",
        city="Beverly Hills",
        state="CA",
        latitude=34.0901,
        longitude=-118.4065,
    )
    db.add(pc2)
    db.commit()
    return pc


# ── Helper: register + return token + user dict ───────────────
def _register_user(client, email="alice@example.com", password="secret123",
                    first_name="Alice", last_name="Smith", nickname="AliceGamer",
                    postal_code="10001", phone_number=None):
    body = {
        "email": email,
        "password": password,
        "first_name": first_name,
        "last_name": last_name,
        "nickname": nickname,
        "postal_code": postal_code,
    }
    if phone_number:
        body["phone_number"] = phone_number
    return client.post("/api/auth/register", json=body)


def _login_user(client, email="alice@example.com", password="secret123"):
    return client.post("/api/auth/login", json={"email": email, "password": password})


def _auth_header(token: str):
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def registered_user(client, seed_postal_code):
    """Register a default user and return (user_dict, token)."""
    res = _register_user(client)
    user = res.json()
    login_res = _login_user(client)
    token = login_res.json()["access_token"]
    return user, token


@pytest.fixture
def second_user(client, seed_postal_code):
    """Register a second user and return (user_dict, token)."""
    res = _register_user(
        client,
        email="bob@example.com",
        first_name="Bob",
        last_name="Jones",
        nickname="BobTrader",
        postal_code="90210",
    )
    user = res.json()
    login_res = _login_user(client, email="bob@example.com")
    token = login_res.json()["access_token"]
    return user, token
