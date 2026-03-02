"""Tests for postal code endpoints: /api/postal-codes/*."""
from tests.conftest import _auth_header


class TestListPostalCodes:

    def test_list_postal_codes(self, client, seed_postal_code):
        res = client.get("/api/postal-codes/")
        assert res.status_code == 200
        data = res.json()
        assert len(data) >= 2

    def test_search_by_prefix(self, client, seed_postal_code):
        res = client.get("/api/postal-codes/?search=100")
        assert res.status_code == 200
        data = res.json()
        assert any(p["postal_code"] == "10001" for p in data)

    def test_search_by_city(self, client, seed_postal_code):
        res = client.get("/api/postal-codes/?search=New York")
        assert res.status_code == 200
        data = res.json()
        assert any(p["city"] == "New York" for p in data)

    def test_search_no_match(self, client, seed_postal_code):
        res = client.get("/api/postal-codes/?search=ZZZZZ")
        assert res.status_code == 200
        assert res.json() == []


class TestGetPostalCode:

    def test_get_by_code(self, client, seed_postal_code):
        res = client.get("/api/postal-codes/10001")
        assert res.status_code == 200
        data = res.json()
        assert data["postal_code"] == "10001"
        assert data["city"] == "New York"
        assert data["state"] == "NY"

    def test_nonexistent_code(self, client, seed_postal_code):
        res = client.get("/api/postal-codes/00000")
        assert res.status_code == 404
