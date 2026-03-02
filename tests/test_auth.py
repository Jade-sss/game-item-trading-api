"""Tests for authentication endpoints: /api/auth/register and /api/auth/login."""
from tests.conftest import _auth_header, _login_user, _register_user


# ── Registration ───────────────────────────────────────────────

class TestRegister:

    def test_register_success(self, client, seed_postal_code):
        res = _register_user(client)
        assert res.status_code == 201
        data = res.json()
        assert data["email"] == "alice@example.com"
        assert data["first_name"] == "Alice"
        assert data["last_name"] == "Smith"
        assert data["nickname"] == "AliceGamer"
        assert data["city"] == "New York"
        assert data["state"] == "NY"
        assert data["postal_code"] == "10001"
        assert "id" in data
        assert "hashed_password" not in data

    def test_register_with_phone(self, client, seed_postal_code):
        res = _register_user(client, phone_number="+1-555-1234")
        assert res.status_code == 201
        assert res.json()["phone_number"] == "+1-555-1234"

    def test_register_duplicate_email(self, client, seed_postal_code):
        _register_user(client)
        res = _register_user(client)  # same email again
        assert res.status_code == 409
        assert "already registered" in res.json()["detail"]

    def test_register_invalid_postal_code(self, client, seed_postal_code):
        res = _register_user(client, postal_code="00000")
        assert res.status_code == 400
        assert "Invalid postal code" in res.json()["detail"]

    def test_register_missing_required_field(self, client, seed_postal_code):
        res = client.post("/api/auth/register", json={
            "email": "test@example.com",
            "password": "secret123",
            # missing first_name, last_name, nickname, postal_code
        })
        assert res.status_code == 422

    def test_register_short_password(self, client, seed_postal_code):
        res = _register_user(client, password="abc")
        assert res.status_code == 422

    def test_register_invalid_email(self, client, seed_postal_code):
        res = _register_user(client, email="not-an-email")
        assert res.status_code == 422

    def test_register_auto_generates_username(self, client, seed_postal_code):
        res = _register_user(client, email="myuser@example.com")
        assert res.status_code == 201
        assert res.json()["username"] == "myuser"

    def test_register_username_collision_appends_number(self, client, seed_postal_code):
        _register_user(client, email="myuser@example.com")
        res = _register_user(client, email="myuser@other.com")
        assert res.status_code == 201
        assert res.json()["username"] == "myuser1"


# ── Login ──────────────────────────────────────────────────────

class TestLogin:

    def test_login_success(self, client, seed_postal_code):
        _register_user(client)
        res = _login_user(client)
        assert res.status_code == 200
        data = res.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, client, seed_postal_code):
        _register_user(client)
        res = _login_user(client, password="wrongpassword")
        assert res.status_code == 401
        assert "Invalid email or password" in res.json()["detail"]

    def test_login_nonexistent_user(self, client, seed_postal_code):
        res = _login_user(client, email="nobody@example.com")
        assert res.status_code == 401

    def test_token_grants_access(self, client, seed_postal_code):
        _register_user(client)
        token = _login_user(client).json()["access_token"]
        res = client.get("/api/users/me", headers=_auth_header(token))
        assert res.status_code == 200
        assert res.json()["email"] == "alice@example.com"

    def test_no_token_returns_401(self, client):
        res = client.get("/api/users/me")
        assert res.status_code == 401

    def test_invalid_token_returns_401(self, client):
        res = client.get("/api/users/me", headers=_auth_header("garbage.token.here"))
        assert res.status_code == 401
