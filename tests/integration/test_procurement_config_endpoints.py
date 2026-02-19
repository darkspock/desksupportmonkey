"""Integration tests for /api/v1/settings/procurement."""


class TestSaveProcurementConfig:
    def test_save_config_admin(
        self, client, auth_as, admin_user,
    ):
        auth_as(admin_user)
        resp = client.put(
            "/api/v1/settings/procurement",
            json={
                "enforcement_mode": "strict",
                "approval_threshold_cents": 50000,
                "po_number_prefix": "PO",
                "fiscal_year_start_month": 7,
                "currency": "USD",
                "auto_create_assets": True,
            },
        )

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["enforcement_mode"] == "strict"
        assert data["approval_threshold_cents"] == 50000
        assert data["po_number_prefix"] == "PO"
        assert data["fiscal_year_start_month"] == 7
        assert data["currency"] == "USD"
        assert data["auto_create_assets"] is True

    def test_save_updates_existing(
        self, client, auth_as, admin_user,
    ):
        auth_as(admin_user)
        # Create
        client.put(
            "/api/v1/settings/procurement",
            json={
                "enforcement_mode": "warn",
                "approval_threshold_cents": 0,
                "po_number_prefix": "PO",
                "fiscal_year_start_month": 1,
                "currency": "USD",
                "auto_create_assets": False,
            },
        )

        # Update
        resp = client.put(
            "/api/v1/settings/procurement",
            json={
                "enforcement_mode": "strict",
                "approval_threshold_cents": 100000,
                "po_number_prefix": "ORD",
                "fiscal_year_start_month": 4,
                "currency": "EUR",
                "auto_create_assets": True,
            },
        )

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["enforcement_mode"] == "strict"
        assert data["approval_threshold_cents"] == 100000
        assert data["po_number_prefix"] == "ORD"
        assert data["currency"] == "EUR"

    def test_invalid_mode_returns_422(
        self, client, auth_as, admin_user,
    ):
        auth_as(admin_user)
        resp = client.put(
            "/api/v1/settings/procurement",
            json={
                "enforcement_mode": "invalid",
                "approval_threshold_cents": 0,
                "po_number_prefix": "PO",
                "fiscal_year_start_month": 1,
                "currency": "USD",
                "auto_create_assets": False,
            },
        )

        assert resp.status_code == 422


class TestGetProcurementConfig:
    def test_get_returns_defaults(
        self, client, auth_as, admin_user,
    ):
        auth_as(admin_user)
        resp = client.get(
            "/api/v1/settings/procurement",
        )

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["enforcement_mode"] == "warn"
        assert data["approval_threshold_cents"] == 0
        assert data["po_number_prefix"] == "PO"
        assert data["currency"] == "USD"

    def test_get_returns_saved_config(
        self, client, auth_as, admin_user,
    ):
        auth_as(admin_user)
        client.put(
            "/api/v1/settings/procurement",
            json={
                "enforcement_mode": "strict",
                "approval_threshold_cents": 75000,
                "po_number_prefix": "COMP",
                "fiscal_year_start_month": 10,
                "currency": "MXN",
                "auto_create_assets": True,
            },
        )

        resp = client.get(
            "/api/v1/settings/procurement",
        )

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["enforcement_mode"] == "strict"
        assert data["approval_threshold_cents"] == 75000
        assert data["currency"] == "MXN"


class TestPermissions:
    def test_technician_cannot_save(
        self, client, auth_as, technician_user,
    ):
        auth_as(technician_user)
        resp = client.put(
            "/api/v1/settings/procurement",
            json={
                "enforcement_mode": "warn",
                "approval_threshold_cents": 0,
                "po_number_prefix": "PO",
                "fiscal_year_start_month": 1,
                "currency": "USD",
                "auto_create_assets": False,
            },
        )

        assert resp.status_code == 403

    def test_technician_cannot_get(
        self, client, auth_as, technician_user,
    ):
        auth_as(technician_user)
        resp = client.get(
            "/api/v1/settings/procurement",
        )

        assert resp.status_code == 403

    def test_employee_cannot_save(
        self, client, auth_as, employee_user,
    ):
        auth_as(employee_user)
        resp = client.put(
            "/api/v1/settings/procurement",
            json={
                "enforcement_mode": "warn",
                "approval_threshold_cents": 0,
                "po_number_prefix": "PO",
                "fiscal_year_start_month": 1,
                "currency": "USD",
                "auto_create_assets": False,
            },
        )

        assert resp.status_code == 403
