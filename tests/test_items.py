"""Tests for item endpoints: /api/items/*."""
from tests.conftest import _auth_header


def _create_item(client, token, **overrides):
    body = {
        "name": "Legendary Sword",
        "game": "World of Warcraft",
        "rarity": "legendary",
        "category": "Weapon",
        "estimated_value": 150.0,
        "description": "A blazing sword",
    }
    body.update(overrides)
    return client.post("/api/items/", headers=_auth_header(token), json=body)


class TestCreateItem:

    def test_create_item(self, client, registered_user):
        _, token = registered_user
        res = _create_item(client, token)
        assert res.status_code == 201
        data = res.json()
        assert data["name"] == "Legendary Sword"
        assert data["game"] == "World of Warcraft"
        assert data["rarity"] == "legendary"
        assert data["is_available"] is True
        assert "id" in data

    def test_create_item_minimal_fields(self, client, registered_user):
        _, token = registered_user
        res = client.post(
            "/api/items/",
            headers=_auth_header(token),
            json={"name": "Simple Item", "game": "Tetris"},
        )
        assert res.status_code == 201
        data = res.json()
        assert data["name"] == "Simple Item"
        assert data["rarity"] is None
        assert data["estimated_value"] is None

    def test_create_item_requires_auth(self, client):
        res = client.post("/api/items/", json={"name": "Sword", "game": "WoW"})
        assert res.status_code == 401

    def test_create_item_missing_name(self, client, registered_user):
        _, token = registered_user
        res = client.post("/api/items/", headers=_auth_header(token), json={"game": "WoW"})
        assert res.status_code == 422


class TestListItems:

    def test_list_items_empty(self, client, seed_postal_code):
        res = client.get("/api/items/")
        assert res.status_code == 200
        assert res.json() == []

    def test_list_items_returns_available(self, client, registered_user):
        _, token = registered_user
        _create_item(client, token, name="Sword")
        _create_item(client, token, name="Shield")
        res = client.get("/api/items/")
        assert res.status_code == 200
        assert len(res.json()) == 2

    def test_list_items_includes_owner_username(self, client, registered_user):
        _, token = registered_user
        _create_item(client, token)
        res = client.get("/api/items/")
        data = res.json()
        assert data[0]["owner_username"] is not None

    def test_filter_by_game(self, client, registered_user):
        _, token = registered_user
        _create_item(client, token, name="Sword", game="WoW")
        _create_item(client, token, name="Ball", game="Rocket League")
        res = client.get("/api/items/?game=WoW")
        data = res.json()
        assert len(data) == 1
        assert data[0]["game"] == "WoW"

    def test_filter_by_rarity(self, client, registered_user):
        _, token = registered_user
        _create_item(client, token, name="CommonItem", rarity="common")
        _create_item(client, token, name="RareItem", rarity="rare")
        res = client.get("/api/items/?rarity=rare")
        assert len(res.json()) == 1
        assert res.json()[0]["name"] == "RareItem"

    def test_search_by_name(self, client, registered_user):
        _, token = registered_user
        _create_item(client, token, name="Dragon Slayer")
        _create_item(client, token, name="Healing Potion")
        res = client.get("/api/items/?search=dragon")
        assert len(res.json()) == 1

    def test_list_my_items(self, client, registered_user, second_user):
        _, token_a = registered_user
        _, token_b = second_user
        _create_item(client, token_a, name="Alice Sword")
        _create_item(client, token_b, name="Bob Shield")
        res = client.get("/api/items/my", headers=_auth_header(token_a))
        assert res.status_code == 200
        names = [i["name"] for i in res.json()]
        assert "Alice Sword" in names
        assert "Bob Shield" not in names


class TestGetItem:

    def test_get_item_by_id(self, client, registered_user):
        _, token = registered_user
        item_id = _create_item(client, token).json()["id"]
        res = client.get(f"/api/items/{item_id}")
        assert res.status_code == 200
        assert res.json()["id"] == item_id

    def test_get_nonexistent_item(self, client, seed_postal_code):
        res = client.get("/api/items/no-such-id")
        assert res.status_code == 404


class TestUpdateItem:

    def test_update_own_item(self, client, registered_user):
        _, token = registered_user
        item_id = _create_item(client, token).json()["id"]
        res = client.put(
            f"/api/items/{item_id}",
            headers=_auth_header(token),
            json={"name": "Updated Name", "rarity": "epic"},
        )
        assert res.status_code == 200
        assert res.json()["name"] == "Updated Name"
        assert res.json()["rarity"] == "epic"

    def test_update_availability(self, client, registered_user):
        _, token = registered_user
        item_id = _create_item(client, token).json()["id"]
        res = client.put(
            f"/api/items/{item_id}",
            headers=_auth_header(token),
            json={"is_available": False},
        )
        assert res.status_code == 200
        assert res.json()["is_available"] is False

    def test_cannot_update_others_item(self, client, registered_user, second_user):
        _, token_a = registered_user
        _, token_b = second_user
        item_id = _create_item(client, token_a).json()["id"]
        res = client.put(
            f"/api/items/{item_id}",
            headers=_auth_header(token_b),
            json={"name": "Hacked"},
        )
        assert res.status_code == 403

    def test_update_nonexistent_item(self, client, registered_user):
        _, token = registered_user
        res = client.put(
            "/api/items/fake-id",
            headers=_auth_header(token),
            json={"name": "X"},
        )
        assert res.status_code == 404


class TestDeleteItem:

    def test_delete_own_item(self, client, registered_user):
        _, token = registered_user
        item_id = _create_item(client, token).json()["id"]
        res = client.delete(f"/api/items/{item_id}", headers=_auth_header(token))
        assert res.status_code == 204
        # Verify gone
        assert client.get(f"/api/items/{item_id}").status_code == 404

    def test_cannot_delete_others_item(self, client, registered_user, second_user):
        _, token_a = registered_user
        _, token_b = second_user
        item_id = _create_item(client, token_a).json()["id"]
        res = client.delete(f"/api/items/{item_id}", headers=_auth_header(token_b))
        assert res.status_code == 403

    def test_delete_nonexistent_item(self, client, registered_user):
        _, token = registered_user
        res = client.delete("/api/items/no-such-id", headers=_auth_header(token))
        assert res.status_code == 404
