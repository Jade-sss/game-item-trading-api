"""Tests for user endpoints: /api/users/*."""
from tests.conftest import _auth_header, _register_user, _login_user


class TestGetProfile:

    def test_get_own_profile(self, client, registered_user):
        user, token = registered_user
        res = client.get("/api/users/me", headers=_auth_header(token))
        assert res.status_code == 200
        data = res.json()
        assert data["email"] == "alice@example.com"
        assert data["nickname"] == "AliceGamer"
        assert data["city"] == "New York"
        assert "average_rating" in data

    def test_get_public_profile(self, client, registered_user):
        user, token = registered_user
        res = client.get(f"/api/users/{user['id']}")
        assert res.status_code == 200
        data = res.json()
        assert data["nickname"] == "AliceGamer"
        # Public profile should NOT include email or phone
        assert "email" not in data
        assert "phone_number" not in data

    def test_get_nonexistent_user(self, client):
        res = client.get("/api/users/nonexistent-id")
        assert res.status_code == 404


class TestUpdateProfile:

    def test_update_nickname(self, client, registered_user):
        user, token = registered_user
        res = client.put(
            "/api/users/me",
            headers=_auth_header(token),
            json={"nickname": "NewNick"},
        )
        assert res.status_code == 200
        assert res.json()["nickname"] == "NewNick"

    def test_update_bio(self, client, registered_user):
        user, token = registered_user
        res = client.put(
            "/api/users/me",
            headers=_auth_header(token),
            json={"bio": "I love trading!"},
        )
        assert res.status_code == 200
        assert res.json()["bio"] == "I love trading!"

    def test_update_postal_code_auto_fills_location(self, client, registered_user):
        user, token = registered_user
        res = client.put(
            "/api/users/me",
            headers=_auth_header(token),
            json={"postal_code": "90210"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["postal_code"] == "90210"
        assert data["city"] == "Beverly Hills"
        assert data["state"] == "CA"

    def test_update_invalid_postal_code(self, client, registered_user):
        user, token = registered_user
        res = client.put(
            "/api/users/me",
            headers=_auth_header(token),
            json={"postal_code": "99999"},
        )
        assert res.status_code == 400

    def test_update_email_conflict(self, client, registered_user, second_user):
        _, token = registered_user
        res = client.put(
            "/api/users/me",
            headers=_auth_header(token),
            json={"email": "bob@example.com"},
        )
        assert res.status_code == 409

    def test_partial_update_preserves_other_fields(self, client, registered_user):
        user, token = registered_user
        client.put(
            "/api/users/me",
            headers=_auth_header(token),
            json={"bio": "Hello"},
        )
        res = client.get("/api/users/me", headers=_auth_header(token))
        data = res.json()
        assert data["bio"] == "Hello"
        assert data["nickname"] == "AliceGamer"  # untouched


class TestChangePassword:

    def test_change_password_success(self, client, registered_user):
        _, token = registered_user
        res = client.put(
            "/api/users/me/password",
            headers=_auth_header(token),
            json={"current_password": "secret123", "new_password": "newpass456"},
        )
        assert res.status_code == 200

        # Old password should no longer work
        login_res = client.post("/api/auth/login", json={
            "email": "alice@example.com", "password": "secret123"
        })
        assert login_res.status_code == 401

        # New password should work
        login_res = client.post("/api/auth/login", json={
            "email": "alice@example.com", "password": "newpass456"
        })
        assert login_res.status_code == 200

    def test_change_password_wrong_current(self, client, registered_user):
        _, token = registered_user
        res = client.put(
            "/api/users/me/password",
            headers=_auth_header(token),
            json={"current_password": "wrongpassword", "new_password": "newpass456"},
        )
        assert res.status_code == 400
        assert "incorrect" in res.json()["detail"]
