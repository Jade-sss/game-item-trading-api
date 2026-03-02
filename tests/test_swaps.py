"""Tests for swap endpoints: /api/swaps/*."""
from tests.conftest import _auth_header


def _create_item(client, token, name="Sword", game="WoW"):
    return client.post(
        "/api/items/",
        headers=_auth_header(token),
        json={"name": name, "game": game, "rarity": "rare"},
    ).json()


def _propose_swap(client, token, receiver_id, offered_ids, requested_ids, message=None):
    body = {
        "receiver_id": receiver_id,
        "offered_item_ids": offered_ids,
        "requested_item_ids": requested_ids,
    }
    if message:
        body["message"] = message
    return client.post("/api/swaps/", headers=_auth_header(token), json=body)


class TestProposeSwap:

    def test_propose_swap_success(self, client, registered_user, second_user):
        user_a, token_a = registered_user
        user_b, token_b = second_user
        item_a = _create_item(client, token_a, "Alice Sword")
        item_b = _create_item(client, token_b, "Bob Shield")

        res = _propose_swap(
            client, token_a, user_b["id"],
            [item_a["id"]], [item_b["id"]],
            message="Let's trade!",
        )
        assert res.status_code == 201
        data = res.json()
        assert data["status"] == "pending"
        assert data["proposer_id"] == user_a["id"]
        assert data["receiver_id"] == user_b["id"]
        assert data["message"] == "Let's trade!"
        assert len(data["offered_items"]) == 1
        assert len(data["requested_items"]) == 1

    def test_cannot_swap_with_self(self, client, registered_user):
        user, token = registered_user
        item = _create_item(client, token)
        res = _propose_swap(client, token, user["id"], [item["id"]], [item["id"]])
        assert res.status_code == 400
        assert "yourself" in res.json()["detail"]

    def test_cannot_offer_others_items(self, client, registered_user, second_user):
        user_a, token_a = registered_user
        user_b, token_b = second_user
        item_b = _create_item(client, token_b, "Bob Item")
        item_b2 = _create_item(client, token_b, "Bob Item2")
        # Alice tries to offer Bob's item
        res = _propose_swap(client, token_a, user_b["id"], [item_b["id"]], [item_b2["id"]])
        assert res.status_code == 400

    def test_swap_nonexistent_receiver(self, client, registered_user):
        _, token = registered_user
        item = _create_item(client, token)
        res = _propose_swap(client, token, "fake-user-id", [item["id"]], [item["id"]])
        assert res.status_code == 404


class TestAcceptSwap:

    def _setup_swap(self, client, registered_user, second_user):
        user_a, token_a = registered_user
        user_b, token_b = second_user
        item_a = _create_item(client, token_a, "Alice Sword")
        item_b = _create_item(client, token_b, "Bob Shield")
        swap_res = _propose_swap(client, token_a, user_b["id"], [item_a["id"]], [item_b["id"]])
        return swap_res.json(), token_a, token_b, item_a, item_b

    def test_accept_swap(self, client, registered_user, second_user):
        swap, token_a, token_b, item_a, item_b = self._setup_swap(client, registered_user, second_user)
        res = client.post(f"/api/swaps/{swap['id']}/accept", headers=_auth_header(token_b))
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "completed"
        assert data["completed_at"] is not None

    def test_accept_transfers_ownership(self, client, registered_user, second_user):
        swap, token_a, token_b, item_a, item_b = self._setup_swap(client, registered_user, second_user)
        client.post(f"/api/swaps/{swap['id']}/accept", headers=_auth_header(token_b))

        # Alice's item should now be owned by Bob
        res = client.get(f"/api/items/{item_a['id']}")
        assert res.json()["owner_id"] == second_user[0]["id"]

        # Bob's item should now be owned by Alice
        res = client.get(f"/api/items/{item_b['id']}")
        assert res.json()["owner_id"] == registered_user[0]["id"]

    def test_proposer_cannot_accept(self, client, registered_user, second_user):
        swap, token_a, token_b, _, _ = self._setup_swap(client, registered_user, second_user)
        res = client.post(f"/api/swaps/{swap['id']}/accept", headers=_auth_header(token_a))
        assert res.status_code == 403

    def test_cannot_accept_non_pending(self, client, registered_user, second_user):
        swap, token_a, token_b, _, _ = self._setup_swap(client, registered_user, second_user)
        client.post(f"/api/swaps/{swap['id']}/reject", headers=_auth_header(token_b))
        res = client.post(f"/api/swaps/{swap['id']}/accept", headers=_auth_header(token_b))
        assert res.status_code == 400


class TestRejectSwap:

    def test_reject_swap(self, client, registered_user, second_user):
        user_a, token_a = registered_user
        user_b, token_b = second_user
        item_a = _create_item(client, token_a, "Sword")
        item_b = _create_item(client, token_b, "Shield")
        swap = _propose_swap(client, token_a, user_b["id"], [item_a["id"]], [item_b["id"]]).json()

        res = client.post(f"/api/swaps/{swap['id']}/reject", headers=_auth_header(token_b))
        assert res.status_code == 200
        assert res.json()["status"] == "rejected"

    def test_proposer_cannot_reject(self, client, registered_user, second_user):
        user_a, token_a = registered_user
        user_b, token_b = second_user
        item_a = _create_item(client, token_a, "Sword")
        item_b = _create_item(client, token_b, "Shield")
        swap = _propose_swap(client, token_a, user_b["id"], [item_a["id"]], [item_b["id"]]).json()

        res = client.post(f"/api/swaps/{swap['id']}/reject", headers=_auth_header(token_a))
        assert res.status_code == 403


class TestCancelSwap:

    def test_cancel_swap(self, client, registered_user, second_user):
        user_a, token_a = registered_user
        user_b, token_b = second_user
        item_a = _create_item(client, token_a, "Sword")
        item_b = _create_item(client, token_b, "Shield")
        swap = _propose_swap(client, token_a, user_b["id"], [item_a["id"]], [item_b["id"]]).json()

        res = client.post(f"/api/swaps/{swap['id']}/cancel", headers=_auth_header(token_a))
        assert res.status_code == 200
        assert res.json()["status"] == "cancelled"

    def test_receiver_cannot_cancel(self, client, registered_user, second_user):
        user_a, token_a = registered_user
        user_b, token_b = second_user
        item_a = _create_item(client, token_a, "Sword")
        item_b = _create_item(client, token_b, "Shield")
        swap = _propose_swap(client, token_a, user_b["id"], [item_a["id"]], [item_b["id"]]).json()

        res = client.post(f"/api/swaps/{swap['id']}/cancel", headers=_auth_header(token_b))
        assert res.status_code == 403


class TestRateSwap:

    def _completed_swap(self, client, registered_user, second_user):
        user_a, token_a = registered_user
        user_b, token_b = second_user
        item_a = _create_item(client, token_a, "Sword")
        item_b = _create_item(client, token_b, "Shield")
        swap = _propose_swap(client, token_a, user_b["id"], [item_a["id"]], [item_b["id"]]).json()
        client.post(f"/api/swaps/{swap['id']}/accept", headers=_auth_header(token_b))
        return swap, token_a, token_b

    def test_proposer_rates_swap(self, client, registered_user, second_user):
        swap, token_a, token_b = self._completed_swap(client, registered_user, second_user)
        res = client.post(
            f"/api/swaps/{swap['id']}/rate",
            headers=_auth_header(token_a),
            json={"rating": 5, "review": "Great trade!"},
        )
        assert res.status_code == 200
        assert res.json()["proposer_rating"] == 5
        assert res.json()["proposer_review"] == "Great trade!"

    def test_receiver_rates_swap(self, client, registered_user, second_user):
        swap, token_a, token_b = self._completed_swap(client, registered_user, second_user)
        res = client.post(
            f"/api/swaps/{swap['id']}/rate",
            headers=_auth_header(token_b),
            json={"rating": 4},
        )
        assert res.status_code == 200
        assert res.json()["receiver_rating"] == 4

    def test_cannot_rate_twice(self, client, registered_user, second_user):
        swap, token_a, _ = self._completed_swap(client, registered_user, second_user)
        client.post(
            f"/api/swaps/{swap['id']}/rate",
            headers=_auth_header(token_a),
            json={"rating": 5},
        )
        res = client.post(
            f"/api/swaps/{swap['id']}/rate",
            headers=_auth_header(token_a),
            json={"rating": 3},
        )
        assert res.status_code == 400
        assert "already rated" in res.json()["detail"]

    def test_cannot_rate_pending_swap(self, client, registered_user, second_user):
        user_a, token_a = registered_user
        user_b, token_b = second_user
        item_a = _create_item(client, token_a, "Sword")
        item_b = _create_item(client, token_b, "Shield")
        swap = _propose_swap(client, token_a, user_b["id"], [item_a["id"]], [item_b["id"]]).json()
        res = client.post(
            f"/api/swaps/{swap['id']}/rate",
            headers=_auth_header(token_a),
            json={"rating": 5},
        )
        assert res.status_code == 400

    def test_rating_updates_user_stats(self, client, registered_user, second_user):
        swap, token_a, token_b = self._completed_swap(client, registered_user, second_user)
        # Proposer rates → updates receiver stats
        client.post(
            f"/api/swaps/{swap['id']}/rate",
            headers=_auth_header(token_a),
            json={"rating": 4},
        )
        receiver_profile = client.get("/api/users/me", headers=_auth_header(token_b)).json()
        assert receiver_profile["rating_count"] == 1
        assert receiver_profile["average_rating"] == 4.0

    def test_invalid_rating_value(self, client, registered_user, second_user):
        swap, token_a, _ = self._completed_swap(client, registered_user, second_user)
        res = client.post(
            f"/api/swaps/{swap['id']}/rate",
            headers=_auth_header(token_a),
            json={"rating": 6},  # above max
        )
        assert res.status_code == 422


class TestSwapHistory:

    def test_history_empty(self, client, registered_user):
        _, token = registered_user
        res = client.get("/api/swaps/history", headers=_auth_header(token))
        assert res.status_code == 200
        assert res.json() == []

    def test_history_returns_user_swaps(self, client, registered_user, second_user):
        user_a, token_a = registered_user
        user_b, token_b = second_user
        item_a = _create_item(client, token_a, "Sword")
        item_b = _create_item(client, token_b, "Shield")
        _propose_swap(client, token_a, user_b["id"], [item_a["id"]], [item_b["id"]])

        res_a = client.get("/api/swaps/history", headers=_auth_header(token_a))
        res_b = client.get("/api/swaps/history", headers=_auth_header(token_b))
        assert len(res_a.json()) == 1
        assert len(res_b.json()) == 1

    def test_history_filter_by_status(self, client, registered_user, second_user):
        user_a, token_a = registered_user
        user_b, token_b = second_user
        item_a = _create_item(client, token_a, "Sword")
        item_b = _create_item(client, token_b, "Shield")
        _propose_swap(client, token_a, user_b["id"], [item_a["id"]], [item_b["id"]])

        res = client.get("/api/swaps/history?status=pending", headers=_auth_header(token_a))
        assert len(res.json()) == 1
        res = client.get("/api/swaps/history?status=completed", headers=_auth_header(token_a))
        assert len(res.json()) == 0


class TestSwapDetail:

    def test_get_swap_detail(self, client, registered_user, second_user):
        user_a, token_a = registered_user
        user_b, token_b = second_user
        item_a = _create_item(client, token_a, "Sword")
        item_b = _create_item(client, token_b, "Shield")
        swap = _propose_swap(client, token_a, user_b["id"], [item_a["id"]], [item_b["id"]]).json()

        res = client.get(f"/api/swaps/{swap['id']}", headers=_auth_header(token_a))
        assert res.status_code == 200
        data = res.json()
        assert len(data["offered_items"]) == 1
        assert len(data["requested_items"]) == 1
        assert data["proposer_username"] is not None

    def test_non_participant_cannot_view(self, client, registered_user, second_user, seed_postal_code):
        from tests.conftest import _register_user, _login_user
        user_a, token_a = registered_user
        user_b, token_b = second_user
        item_a = _create_item(client, token_a, "Sword")
        item_b = _create_item(client, token_b, "Shield")
        swap = _propose_swap(client, token_a, user_b["id"], [item_a["id"]], [item_b["id"]]).json()

        # Register a third user
        _register_user(client, email="eve@example.com", first_name="Eve", last_name="Evil", nickname="Eve3")
        token_eve = _login_user(client, email="eve@example.com").json()["access_token"]

        res = client.get(f"/api/swaps/{swap['id']}", headers=_auth_header(token_eve))
        assert res.status_code == 403

    def test_swap_not_found(self, client, registered_user):
        _, token = registered_user
        res = client.get("/api/swaps/fake-swap-id", headers=_auth_header(token))
        assert res.status_code == 404
