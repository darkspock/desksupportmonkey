"""Integration tests for auto-assignment on request creation."""


class TestAutoAssignment:
    def test_request_creation_triggers_auto_assign(
        self, client, auth_as, db_session, company,
        make_user,
    ):
        """new_equipment request with profile → auto_assignment."""
        from src.asset_bc.asset.domain.entities import Asset
        from src.asset_bc.asset.domain.enums import (
            AssetType,
        )
        from src.asset_bc.asset.infrastructure.repository import (  # noqa: E501
            AssetRepository,
        )
        from src.auth_bc.user.domain.enums import UserRole
        from src.company_bc.department.domain.entities import (
            Department,
        )
        from src.company_bc.department.infrastructure.repository import (  # noqa: E501
            DepartmentRepository,
        )
        from src.company_bc.equipment_profile.domain.entities import (  # noqa: E501
            EquipmentProfile,
            EquipmentProfileItem,
        )
        from src.company_bc.equipment_profile.infrastructure.repository import (  # noqa: E501
            EquipmentProfileRepository,
        )

        # Create department
        dept = Department.create(
            company_id=company.id, name="Engineering",
        )
        DepartmentRepository(db_session).save(dept)
        db_session.flush()

        # Create employee in that department
        user = make_user(
            email="autoassign@testco.com",
            role=UserRole.EMPLOYEE,
            company_id=company.id,
            department_id=dept.id,
        )

        # Create equipment profile
        profile = EquipmentProfile.create(
            company_id=company.id,
            department_id=dept.id,
            role=UserRole.EMPLOYEE,
        )
        profile.items = [
            EquipmentProfileItem(
                id="item-1",
                profile_id=profile.id,
                asset_type=AssetType.LAPTOP,
                quantity=1,
            ),
        ]
        EquipmentProfileRepository(db_session).save(profile)
        db_session.flush()

        # Create in-stock laptop
        asset = Asset.create(
            company_id=company.id,
            type=AssetType.LAPTOP,
            brand="Dell",
            model="Latitude 5540",
            serial_number="AUTO-001",
        )
        AssetRepository(db_session).save(asset)
        db_session.flush()

        # Create request
        auth_as(user)
        resp = client.post(
            "/api/v1/requests",
            json={
                "type": "new_equipment",
                "title": "Need a laptop",
                "description": "New hire laptop request",
            },
        )

        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["data"] is not None
        auto = data["data"]["auto_assignment"]
        assert auto["status"] == "matched"
        assert len(auto["matched_assets"]) == 1
        assert auto["matched_assets"][0]["asset_id"] == asset.id

    def test_request_with_no_profile_stores_fallback(
        self, client, auth_as, db_session, company,
        make_user,
    ):
        """new_equipment request with no profile → fallback metadata."""
        from src.auth_bc.user.domain.enums import UserRole
        from src.company_bc.department.domain.entities import (
            Department,
        )
        from src.company_bc.department.infrastructure.repository import (  # noqa: E501
            DepartmentRepository,
        )

        dept = Department.create(
            company_id=company.id, name="NoProfile Dept",
        )
        DepartmentRepository(db_session).save(dept)
        db_session.flush()

        user = make_user(
            email="noauto@testco.com",
            role=UserRole.EMPLOYEE,
            company_id=company.id,
            department_id=dept.id,
        )

        auth_as(user)
        resp = client.post(
            "/api/v1/requests",
            json={
                "type": "new_equipment",
                "title": "Need equipment",
                "description": "Equipment request",
            },
        )

        assert resp.status_code == 201
        data = resp.json()["data"]
        auto = data["data"]["auto_assignment"]
        assert auto["status"] == "fallback"
        assert "no_active_profile" in auto["reasons"]

    def test_incident_request_no_auto_assign(
        self, client, auth_as, employee_user,
    ):
        """Incident requests do not trigger auto-assign."""
        auth_as(employee_user)
        resp = client.post(
            "/api/v1/requests",
            json={
                "type": "incident",
                "title": "Printer broken",
                "description": "The printer is not working",
            },
        )

        assert resp.status_code == 201
        data = resp.json()["data"]
        # No auto_assignment key in data for incidents
        if data["data"]:
            assert "auto_assignment" not in data["data"]
