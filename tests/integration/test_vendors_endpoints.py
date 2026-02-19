"""Integration tests for /api/v1/vendors."""


class TestCreateVendor:
    def test_create_vendor_technician(
        self, client, auth_as, technician_user,
    ):
        auth_as(technician_user)
        resp = client.post(
            "/api/v1/vendors",
            json={
                "name": "Acme Corp",
                "contact_email": "sales@acme.com",
                "phone": "+1-555-0100",
            },
        )

        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["name"] == "Acme Corp"
        assert data["contact_email"] == "sales@acme.com"
        assert data["phone"] == "+1-555-0100"
        assert data["is_active"] is True

    def test_create_vendor_admin(
        self, client, auth_as, admin_user,
    ):
        auth_as(admin_user)
        resp = client.post(
            "/api/v1/vendors",
            json={"name": "Beta Supplies"},
        )

        assert resp.status_code == 201
        assert resp.json()["data"]["name"] == "Beta Supplies"

    def test_create_duplicate_name(
        self, client, auth_as, technician_user,
    ):
        auth_as(technician_user)
        client.post(
            "/api/v1/vendors",
            json={"name": "Unique Vendor"},
        )

        resp = client.post(
            "/api/v1/vendors",
            json={"name": "Unique Vendor"},
        )

        assert resp.status_code == 409

    def test_create_empty_name(
        self, client, auth_as, technician_user,
    ):
        auth_as(technician_user)
        resp = client.post(
            "/api/v1/vendors",
            json={"name": ""},
        )

        assert resp.status_code == 422


class TestListVendors:
    def test_list_vendors(
        self, client, auth_as, technician_user,
    ):
        auth_as(technician_user)
        client.post(
            "/api/v1/vendors",
            json={"name": "Vendor A"},
        )
        client.post(
            "/api/v1/vendors",
            json={"name": "Vendor B"},
        )

        resp = client.get("/api/v1/vendors")

        assert resp.status_code == 200
        assert resp.json()["meta"]["total"] >= 2

    def test_list_with_search(
        self, client, auth_as, technician_user,
    ):
        auth_as(technician_user)
        client.post(
            "/api/v1/vendors",
            json={"name": "Searchable Corp"},
        )

        resp = client.get(
            "/api/v1/vendors?search=Searchable",
        )

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert any(
            v["name"] == "Searchable Corp" for v in data
        )

    def test_list_filter_active(
        self, client, auth_as, admin_user,
    ):
        auth_as(admin_user)
        create_resp = client.post(
            "/api/v1/vendors",
            json={"name": "Active Filter Test"},
        )
        vendor_id = create_resp.json()["data"]["id"]

        # Deactivate
        client.post(
            f"/api/v1/vendors/{vendor_id}/deactivate",
        )

        resp = client.get(
            "/api/v1/vendors?is_active=true",
        )

        assert resp.status_code == 200
        ids = [v["id"] for v in resp.json()["data"]]
        assert vendor_id not in ids


class TestGetVendor:
    def test_get_vendor(
        self, client, auth_as, technician_user,
    ):
        auth_as(technician_user)
        create_resp = client.post(
            "/api/v1/vendors",
            json={
                "name": "Get Test Vendor",
                "contact_email": "info@gettest.com",
            },
        )
        vendor_id = create_resp.json()["data"]["id"]

        resp = client.get(
            f"/api/v1/vendors/{vendor_id}",
        )

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["name"] == "Get Test Vendor"
        assert data["contact_email"] == "info@gettest.com"

    def test_get_not_found(
        self, client, auth_as, technician_user,
    ):
        auth_as(technician_user)
        resp = client.get(
            "/api/v1/vendors/nonexistent",
        )

        assert resp.status_code == 404


class TestUpdateVendor:
    def test_update_vendor(
        self, client, auth_as, technician_user,
    ):
        auth_as(technician_user)
        create_resp = client.post(
            "/api/v1/vendors",
            json={"name": "Old Name"},
        )
        vendor_id = create_resp.json()["data"]["id"]

        resp = client.put(
            f"/api/v1/vendors/{vendor_id}",
            json={
                "name": "New Name",
                "contact_email": "new@vendor.com",
                "notes": "Updated notes",
            },
        )

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["name"] == "New Name"
        assert data["contact_email"] == "new@vendor.com"
        assert data["notes"] == "Updated notes"

    def test_update_not_found(
        self, client, auth_as, technician_user,
    ):
        auth_as(technician_user)
        resp = client.put(
            "/api/v1/vendors/nonexistent",
            json={"name": "Name"},
        )

        assert resp.status_code == 404


class TestActivateDeactivate:
    def test_deactivate_and_activate(
        self, client, auth_as, admin_user,
    ):
        auth_as(admin_user)
        create_resp = client.post(
            "/api/v1/vendors",
            json={"name": "Toggle Vendor"},
        )
        vendor_id = create_resp.json()["data"]["id"]

        # Deactivate
        resp = client.post(
            f"/api/v1/vendors/{vendor_id}/deactivate",
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["is_active"] is False

        # Re-activate
        resp = client.post(
            f"/api/v1/vendors/{vendor_id}/activate",
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["is_active"] is True


class TestPermissions:
    def test_employee_cannot_create(
        self, client, auth_as, employee_user,
    ):
        auth_as(employee_user)
        resp = client.post(
            "/api/v1/vendors",
            json={"name": "Forbidden Vendor"},
        )

        assert resp.status_code == 403

    def test_employee_cannot_list(
        self, client, auth_as, employee_user,
    ):
        auth_as(employee_user)
        resp = client.get("/api/v1/vendors")

        assert resp.status_code == 403

    def test_technician_cannot_activate(
        self, client, auth_as, technician_user,
    ):
        auth_as(technician_user)
        create_resp = client.post(
            "/api/v1/vendors",
            json={"name": "Perm Test Vendor"},
        )
        vendor_id = create_resp.json()["data"]["id"]

        resp = client.post(
            f"/api/v1/vendors/{vendor_id}/deactivate",
        )

        assert resp.status_code == 403


class TestTenantIsolation:
    def test_cannot_see_other_company_vendor(
        self, client, auth_as, technician_user,
        db_session, make_user,
    ):
        from src.auth_bc.user.domain.enums import UserRole
        from src.company_bc.company.domain.entities import (
            Company,
        )
        from src.company_bc.company.infrastructure.repository import (
            CompanyRepository,
        )

        # Create vendor as technician of company A
        auth_as(technician_user)
        create_resp = client.post(
            "/api/v1/vendors",
            json={"name": "Company A Vendor"},
        )
        vendor_id = create_resp.json()["data"]["id"]

        # Create another company + user
        other_company = Company.create(
            name="Other Co",
            email_domains=["other.com"],
        )
        CompanyRepository(db_session).save(other_company)
        CompanyRepository(db_session).save_domains(
            other_company.id, other_company.email_domains,
        )
        db_session.flush()

        other_tech = make_user(
            "tech@other.com",
            role=UserRole.TECHNICIAN,
            company_id=other_company.id,
        )

        # Try to access vendor from other company
        auth_as(other_tech)
        resp = client.get(
            f"/api/v1/vendors/{vendor_id}",
        )

        assert resp.status_code == 404
