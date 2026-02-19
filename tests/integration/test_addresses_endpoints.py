"""Integration tests for /api/v1/addresses endpoints."""

import pytest


def _create_address(
    client, label="HQ Office", **kwargs,
):
    """Create an address and return the response."""
    payload = {
        "label": label,
        "street_line_1": "123 Main St",
        "city": "Austin",
        "state": "TX",
        "postal_code": "78701",
        **kwargs,
    }
    return client.post("/api/v1/addresses", json=payload)


class TestCreateAddress:
    def test_create_address_returns_201(
        self, client, auth_as, technician_user,
    ):
        auth_as(technician_user)

        resp = _create_address(client)

        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["label"] == "HQ Office"
        assert data["country"] == "US"
        assert data["is_active"] is True
        assert data["is_office"] is False


class TestListAddresses:
    def test_list_addresses_returns_200(
        self, client, auth_as, technician_user,
    ):
        auth_as(technician_user)
        _create_address(client, label="Addr List 1")

        resp = client.get("/api/v1/addresses")
        assert resp.status_code == 200
        body = resp.json()
        assert "data" in body
        assert "meta" in body
        assert body["meta"]["total"] >= 1


class TestGetAddress:
    def test_get_address_returns_200(
        self, client, auth_as, technician_user,
    ):
        auth_as(technician_user)
        create_resp = _create_address(
            client, label="Addr Get",
        )
        addr_id = create_resp.json()["data"]["id"]

        resp = client.get(
            f"/api/v1/addresses/{addr_id}",
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["id"] == addr_id


class TestUpdateAddress:
    def test_update_address_returns_200(
        self, client, auth_as, technician_user,
    ):
        auth_as(technician_user)
        create_resp = _create_address(
            client, label="Old Label",
        )
        addr_id = create_resp.json()["data"]["id"]

        resp = client.put(
            f"/api/v1/addresses/{addr_id}",
            json={
                "label": "New Label",
                "city": "Dallas",
            },
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["label"] == "New Label"
        assert data["city"] == "Dallas"
        assert data["state"] == "TX"  # unchanged


class TestDeactivateAddress:
    def test_deactivate_address_returns_200(
        self, client, auth_as, technician_user,
    ):
        auth_as(technician_user)
        create_resp = _create_address(
            client, label="To Deactivate",
        )
        addr_id = create_resp.json()["data"]["id"]

        resp = client.delete(
            f"/api/v1/addresses/{addr_id}",
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["is_active"] is False

    def test_deactivated_not_in_list(
        self, client, auth_as, technician_user,
    ):
        auth_as(technician_user)
        create_resp = _create_address(
            client, label="Will Hide",
        )
        addr_id = create_resp.json()["data"]["id"]

        client.delete(f"/api/v1/addresses/{addr_id}")

        resp = client.get("/api/v1/addresses")
        ids = [
            a["id"] for a in resp.json()["data"]
        ]
        assert addr_id not in ids

    def test_deactivated_still_accessible_by_id(
        self, client, auth_as, technician_user,
    ):
        auth_as(technician_user)
        create_resp = _create_address(
            client, label="Still Visible",
        )
        addr_id = create_resp.json()["data"]["id"]

        client.delete(f"/api/v1/addresses/{addr_id}")

        resp = client.get(
            f"/api/v1/addresses/{addr_id}",
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["is_active"] is False


class TestAddressesByUser:
    def test_addresses_by_user_returns_200(
        self, client, auth_as, technician_user,
        employee_user,
    ):
        auth_as(technician_user)
        _create_address(
            client,
            label="Employee Home",
            user_id=employee_user.id,
        )

        resp = client.get(
            f"/api/v1/addresses/by-user/{employee_user.id}",
        )
        assert resp.status_code == 200
        assert len(resp.json()["data"]) >= 1
