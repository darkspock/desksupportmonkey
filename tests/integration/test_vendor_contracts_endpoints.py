"""Integration tests for /api/v1/vendors/{vendor_id}/contracts."""


def _create_vendor(client, name="Test Vendor"):
    resp = client.post(
        "/api/v1/vendors",
        json={"name": name},
    )
    return resp.json()["data"]["id"]


class TestCreateContract:
    def test_create_contract_admin(
        self, client, auth_as, admin_user,
    ):
        auth_as(admin_user)
        vendor_id = _create_vendor(client)

        resp = client.post(
            f"/api/v1/vendors/{vendor_id}/contracts",
            json={
                "contract_type": "saas",
                "title": "SaaS License",
                "start_date": "2026-01-01",
                "end_date": "2026-12-31",
                "annual_value": "12000.00",
                "currency": "EUR",
            },
        )

        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["title"] == "SaaS License"
        assert data["contract_type"] == "saas"
        assert data["status"] == "draft"
        assert data["annual_value"] == "12000.00"

    def test_create_with_security_clauses(
        self, client, auth_as, admin_user,
    ):
        auth_as(admin_user)
        vendor_id = _create_vendor(client)

        resp = client.post(
            f"/api/v1/vendors/{vendor_id}/contracts",
            json={
                "contract_type": "service",
                "title": "Secure Service",
                "start_date": "2026-01-01",
                "security_clauses": {
                    "data_protection": True,
                    "incident_notification": True,
                },
            },
        )

        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["security_clauses"]["data_protection"] is True

    def test_create_vendor_not_found(
        self, client, auth_as, admin_user,
    ):
        auth_as(admin_user)
        resp = client.post(
            "/api/v1/vendors/nonexistent/contracts",
            json={
                "contract_type": "service",
                "title": "Test",
                "start_date": "2026-01-01",
            },
        )
        assert resp.status_code == 404

    def test_create_invalid_type(
        self, client, auth_as, admin_user,
    ):
        auth_as(admin_user)
        vendor_id = _create_vendor(client)

        resp = client.post(
            f"/api/v1/vendors/{vendor_id}/contracts",
            json={
                "contract_type": "invalid",
                "title": "Test",
                "start_date": "2026-01-01",
            },
        )
        assert resp.status_code == 422


class TestListContracts:
    def test_list_contracts(
        self, client, auth_as, admin_user,
    ):
        auth_as(admin_user)
        vendor_id = _create_vendor(client)

        client.post(
            f"/api/v1/vendors/{vendor_id}/contracts",
            json={
                "contract_type": "service",
                "title": "Contract A",
                "start_date": "2026-01-01",
            },
        )
        client.post(
            f"/api/v1/vendors/{vendor_id}/contracts",
            json={
                "contract_type": "saas",
                "title": "Contract B",
                "start_date": "2026-06-01",
            },
        )

        resp = client.get(
            f"/api/v1/vendors/{vendor_id}/contracts",
        )

        assert resp.status_code == 200
        assert resp.json()["meta"]["total"] >= 2

    def test_list_filter_status(
        self, client, auth_as, admin_user,
    ):
        auth_as(admin_user)
        vendor_id = _create_vendor(client)

        create_resp = client.post(
            f"/api/v1/vendors/{vendor_id}/contracts",
            json={
                "contract_type": "service",
                "title": "Active One",
                "start_date": "2026-01-01",
            },
        )
        contract_id = create_resp.json()["data"]["id"]

        # Activate the contract
        client.post(
            f"/api/v1/vendors/{vendor_id}/contracts"
            f"/{contract_id}/change-status",
            json={"status": "active"},
        )

        resp = client.get(
            f"/api/v1/vendors/{vendor_id}/contracts"
            "?status=active",
        )

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert all(c["status"] == "active" for c in data)

    def test_technician_can_list(
        self, client, auth_as, technician_user,
    ):
        auth_as(technician_user)
        vendor_id = _create_vendor(client)

        resp = client.get(
            f"/api/v1/vendors/{vendor_id}/contracts",
        )
        assert resp.status_code == 200


class TestGetContract:
    def test_get_contract(
        self, client, auth_as, admin_user,
    ):
        auth_as(admin_user)
        vendor_id = _create_vendor(client)

        create_resp = client.post(
            f"/api/v1/vendors/{vendor_id}/contracts",
            json={
                "contract_type": "licensing",
                "title": "Software License",
                "start_date": "2026-01-01",
            },
        )
        contract_id = create_resp.json()["data"]["id"]

        resp = client.get(
            f"/api/v1/vendors/{vendor_id}/contracts"
            f"/{contract_id}",
        )

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["title"] == "Software License"
        assert data["document_count"] == 0

    def test_get_not_found(
        self, client, auth_as, admin_user,
    ):
        auth_as(admin_user)
        vendor_id = _create_vendor(client)

        resp = client.get(
            f"/api/v1/vendors/{vendor_id}/contracts"
            "/nonexistent",
        )
        assert resp.status_code == 404


class TestUpdateContract:
    def test_update_contract(
        self, client, auth_as, admin_user,
    ):
        auth_as(admin_user)
        vendor_id = _create_vendor(client)

        create_resp = client.post(
            f"/api/v1/vendors/{vendor_id}/contracts",
            json={
                "contract_type": "service",
                "title": "Original",
                "start_date": "2026-01-01",
            },
        )
        contract_id = create_resp.json()["data"]["id"]

        resp = client.put(
            f"/api/v1/vendors/{vendor_id}/contracts"
            f"/{contract_id}",
            json={
                "title": "Updated Title",
                "annual_value": "5000.00",
                "currency": "USD",
            },
        )

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["title"] == "Updated Title"
        assert data["annual_value"] == "5000.00"

    def test_update_not_found(
        self, client, auth_as, admin_user,
    ):
        auth_as(admin_user)
        vendor_id = _create_vendor(client)

        resp = client.put(
            f"/api/v1/vendors/{vendor_id}/contracts"
            "/nonexistent",
            json={"title": "New"},
        )
        assert resp.status_code == 404


class TestChangeStatus:
    def test_draft_to_active(
        self, client, auth_as, admin_user,
    ):
        auth_as(admin_user)
        vendor_id = _create_vendor(client)

        create_resp = client.post(
            f"/api/v1/vendors/{vendor_id}/contracts",
            json={
                "contract_type": "service",
                "title": "Status Test",
                "start_date": "2026-01-01",
            },
        )
        contract_id = create_resp.json()["data"]["id"]

        resp = client.post(
            f"/api/v1/vendors/{vendor_id}/contracts"
            f"/{contract_id}/change-status",
            json={"status": "active"},
        )

        assert resp.status_code == 200
        assert resp.json()["data"]["status"] == "active"

    def test_invalid_transition(
        self, client, auth_as, admin_user,
    ):
        auth_as(admin_user)
        vendor_id = _create_vendor(client)

        create_resp = client.post(
            f"/api/v1/vendors/{vendor_id}/contracts",
            json={
                "contract_type": "service",
                "title": "Status Test",
                "start_date": "2026-01-01",
            },
        )
        contract_id = create_resp.json()["data"]["id"]

        resp = client.post(
            f"/api/v1/vendors/{vendor_id}/contracts"
            f"/{contract_id}/change-status",
            json={"status": "expired"},
        )

        assert resp.status_code == 422


class TestDeleteContract:
    def test_soft_delete(
        self, client, auth_as, admin_user,
    ):
        auth_as(admin_user)
        vendor_id = _create_vendor(client)

        create_resp = client.post(
            f"/api/v1/vendors/{vendor_id}/contracts",
            json={
                "contract_type": "service",
                "title": "Delete Test",
                "start_date": "2026-01-01",
            },
        )
        contract_id = create_resp.json()["data"]["id"]

        resp = client.delete(
            f"/api/v1/vendors/{vendor_id}/contracts"
            f"/{contract_id}",
        )

        assert resp.status_code == 204

        # Should not appear in list
        list_resp = client.get(
            f"/api/v1/vendors/{vendor_id}/contracts",
        )
        ids = [c["id"] for c in list_resp.json()["data"]]
        assert contract_id not in ids

    def test_delete_not_found(
        self, client, auth_as, admin_user,
    ):
        auth_as(admin_user)
        vendor_id = _create_vendor(client)

        resp = client.delete(
            f"/api/v1/vendors/{vendor_id}/contracts"
            "/nonexistent",
        )
        assert resp.status_code == 404


class TestPermissions:
    def test_employee_cannot_create(
        self, client, auth_as, employee_user,
    ):
        auth_as(employee_user)
        resp = client.post(
            "/api/v1/vendors/v1/contracts",
            json={
                "contract_type": "service",
                "title": "Test",
                "start_date": "2026-01-01",
            },
        )
        assert resp.status_code == 403

    def test_technician_cannot_create(
        self, client, auth_as, technician_user,
    ):
        auth_as(technician_user)
        vendor_id = _create_vendor(client)

        resp = client.post(
            f"/api/v1/vendors/{vendor_id}/contracts",
            json={
                "contract_type": "service",
                "title": "Test",
                "start_date": "2026-01-01",
            },
        )
        assert resp.status_code == 403

    def test_technician_cannot_delete(
        self, client, auth_as, technician_user, admin_user,
    ):
        auth_as(admin_user)
        vendor_id = _create_vendor(client)
        create_resp = client.post(
            f"/api/v1/vendors/{vendor_id}/contracts",
            json={
                "contract_type": "service",
                "title": "Test",
                "start_date": "2026-01-01",
            },
        )
        contract_id = create_resp.json()["data"]["id"]

        auth_as(technician_user)
        resp = client.delete(
            f"/api/v1/vendors/{vendor_id}/contracts"
            f"/{contract_id}",
        )
        assert resp.status_code == 403


class TestTenantIsolation:
    def test_cannot_see_other_company_contract(
        self, client, auth_as, admin_user,
        db_session, make_user,
    ):
        from src.auth_bc.user.domain.enums import UserRole
        from src.company_bc.company.domain.entities import (
            Company,
        )
        from src.company_bc.company.infrastructure.repository import (
            CompanyRepository,
        )

        auth_as(admin_user)
        vendor_id = _create_vendor(client)
        create_resp = client.post(
            f"/api/v1/vendors/{vendor_id}/contracts",
            json={
                "contract_type": "service",
                "title": "Secret Contract",
                "start_date": "2026-01-01",
            },
        )
        contract_id = create_resp.json()["data"]["id"]

        other_company = Company.create(
            name="Other Co",
            email_domains=["otherco.com"],
        )
        CompanyRepository(db_session).save(other_company)
        CompanyRepository(db_session).save_domains(
            other_company.id, other_company.email_domains,
        )
        db_session.flush()

        other_admin = make_user(
            "admin@otherco.com",
            role=UserRole.ADMIN,
            company_id=other_company.id,
        )

        auth_as(other_admin)
        resp = client.get(
            f"/api/v1/vendors/{vendor_id}/contracts"
            f"/{contract_id}",
        )
        assert resp.status_code == 404
