"""Integration tests for /api/v1/purchase-orders."""
import pytest

from src.company_bc.department.domain.entities import Department
from src.company_bc.department.infrastructure.repository import (
    DepartmentRepository,
)


@pytest.fixture()
def department(db_session, company):
    d = Department.create(
        name="Engineering",
        company_id=company.id,
    )
    d.budget_enforcement_enabled = True
    DepartmentRepository(db_session).save(d)
    db_session.flush()
    return d


def _po_payload(department_id: str, **overrides):
    defaults = {
        "vendor_name": "Test Vendor",
        "department_id": department_id,
        "items": [
            {
                "description": "Laptop Dell",
                "asset_type": "laptop",
                "quantity": 2,
                "unit_cost_cents": 50000,
            },
        ],
        "request_ids": [],
        "notes": "Test PO",
    }
    defaults.update(overrides)
    return defaults


class TestCreatePO:
    def test_create_po_technician(
        self, client, auth_as, technician_user, department,
    ):
        auth_as(technician_user)
        resp = client.post(
            "/api/v1/purchase-orders",
            json=_po_payload(department.id),
        )

        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["status"] == "DRAFT"
        assert data["vendor_name"] == "Test Vendor"
        assert len(data["items"]) == 1
        assert data["items"][0]["total_cost_cents"] == 100000
        assert data["total_amount_cents"] == 100000
        assert data["po_number"].startswith("PO-")

    def test_create_po_admin(
        self, client, auth_as, admin_user, department,
    ):
        auth_as(admin_user)
        resp = client.post(
            "/api/v1/purchase-orders",
            json=_po_payload(department.id),
        )
        assert resp.status_code == 201

    def test_create_po_employee_forbidden(
        self, client, auth_as, employee_user, department,
    ):
        auth_as(employee_user)
        resp = client.post(
            "/api/v1/purchase-orders",
            json=_po_payload(department.id),
        )
        assert resp.status_code == 403


class TestListPOs:
    def test_list_pos(
        self, client, auth_as, technician_user, department,
    ):
        auth_as(technician_user)
        client.post(
            "/api/v1/purchase-orders",
            json=_po_payload(department.id),
        )
        client.post(
            "/api/v1/purchase-orders",
            json=_po_payload(department.id),
        )

        resp = client.get("/api/v1/purchase-orders")
        assert resp.status_code == 200
        assert len(resp.json()["data"]) == 2
        assert resp.json()["meta"]["total"] == 2

    def test_list_with_status_filter(
        self, client, auth_as, technician_user, department,
    ):
        auth_as(technician_user)
        client.post(
            "/api/v1/purchase-orders",
            json=_po_payload(department.id),
        )

        resp = client.get(
            "/api/v1/purchase-orders?status=SUBMITTED",
        )
        assert resp.status_code == 200
        assert len(resp.json()["data"]) == 0


class TestGetPO:
    def test_get_po_detail(
        self, client, auth_as, technician_user, department,
    ):
        auth_as(technician_user)
        create_resp = client.post(
            "/api/v1/purchase-orders",
            json=_po_payload(department.id),
        )
        po_id = create_resp.json()["data"]["id"]

        resp = client.get(
            f"/api/v1/purchase-orders/{po_id}",
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["id"] == po_id
        assert len(data["items"]) == 1

    def test_get_po_not_found(
        self, client, auth_as, technician_user,
    ):
        auth_as(technician_user)
        resp = client.get(
            "/api/v1/purchase-orders/nonexistent",
        )
        assert resp.status_code == 404


class TestUpdatePO:
    def test_update_draft_po(
        self, client, auth_as, technician_user, department,
    ):
        auth_as(technician_user)
        create_resp = client.post(
            "/api/v1/purchase-orders",
            json=_po_payload(department.id),
        )
        po_id = create_resp.json()["data"]["id"]

        resp = client.put(
            f"/api/v1/purchase-orders/{po_id}",
            json=_po_payload(
                department.id,
                vendor_name="Updated Vendor",
                items=[
                    {
                        "description": "Monitor",
                        "quantity": 3,
                        "unit_cost_cents": 20000,
                    },
                ],
            ),
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["vendor_name"] == "Updated Vendor"
        assert data["total_amount_cents"] == 60000

    def test_update_non_draft_returns_409(
        self, client, auth_as, technician_user, department,
    ):
        auth_as(technician_user)
        create_resp = client.post(
            "/api/v1/purchase-orders",
            json=_po_payload(department.id),
        )
        po_id = create_resp.json()["data"]["id"]

        # Submit first
        client.post(
            f"/api/v1/purchase-orders/{po_id}/submit",
        )

        resp = client.put(
            f"/api/v1/purchase-orders/{po_id}",
            json=_po_payload(department.id),
        )
        assert resp.status_code == 409


class TestSubmitPO:
    def test_submit_po(
        self, client, auth_as, technician_user, department,
    ):
        auth_as(technician_user)
        create_resp = client.post(
            "/api/v1/purchase-orders",
            json=_po_payload(department.id),
        )
        po_id = create_resp.json()["data"]["id"]

        resp = client.post(
            f"/api/v1/purchase-orders/{po_id}/submit",
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["status"] == "SUBMITTED"

    def test_submit_with_auto_approval(
        self, client, auth_as, technician_user, department,
        db_session,
    ):
        """When PO total is below threshold, auto-approve."""
        from src.procurement_bc.budget.domain.entities import (
            CompanyProcurementConfig,
        )
        from src.procurement_bc.budget.infrastructure.repository import (
            CompanyProcurementConfigRepository,
        )

        config = CompanyProcurementConfig.create(
            company_id=technician_user.company_id,
        )
        config.approval_threshold_cents = 200000
        CompanyProcurementConfigRepository(
            db_session,
        ).save(config)
        db_session.flush()

        auth_as(technician_user)
        create_resp = client.post(
            "/api/v1/purchase-orders",
            json=_po_payload(department.id),
        )
        po_id = create_resp.json()["data"]["id"]

        resp = client.post(
            f"/api/v1/purchase-orders/{po_id}/submit",
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["status"] == "APPROVED"


class TestApprovePO:
    def test_approve_submitted_po(
        self, client, auth_as, technician_user,
        admin_user, department,
    ):
        auth_as(technician_user)
        create_resp = client.post(
            "/api/v1/purchase-orders",
            json=_po_payload(department.id),
        )
        po_id = create_resp.json()["data"]["id"]
        client.post(
            f"/api/v1/purchase-orders/{po_id}/submit",
        )

        auth_as(admin_user)
        resp = client.post(
            f"/api/v1/purchase-orders/{po_id}/approve",
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["status"] == "APPROVED"

    def test_approve_as_technician_forbidden(
        self, client, auth_as, technician_user, department,
    ):
        auth_as(technician_user)
        create_resp = client.post(
            "/api/v1/purchase-orders",
            json=_po_payload(department.id),
        )
        po_id = create_resp.json()["data"]["id"]
        client.post(
            f"/api/v1/purchase-orders/{po_id}/submit",
        )

        resp = client.post(
            f"/api/v1/purchase-orders/{po_id}/approve",
        )
        assert resp.status_code == 403


class TestRejectPO:
    def test_reject_with_reason(
        self, client, auth_as, technician_user,
        admin_user, department,
    ):
        auth_as(technician_user)
        create_resp = client.post(
            "/api/v1/purchase-orders",
            json=_po_payload(department.id),
        )
        po_id = create_resp.json()["data"]["id"]
        client.post(
            f"/api/v1/purchase-orders/{po_id}/submit",
        )

        auth_as(admin_user)
        resp = client.post(
            f"/api/v1/purchase-orders/{po_id}/reject",
            json={"reason": "Over budget"},
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["status"] == "CANCELLED"
        assert data["cancellation_reason"] == "Over budget"


class TestMarkOrdered:
    def test_mark_ordered(
        self, client, auth_as, technician_user,
        admin_user, department,
    ):
        auth_as(technician_user)
        create_resp = client.post(
            "/api/v1/purchase-orders",
            json=_po_payload(department.id),
        )
        po_id = create_resp.json()["data"]["id"]
        client.post(
            f"/api/v1/purchase-orders/{po_id}/submit",
        )

        auth_as(admin_user)
        client.post(
            f"/api/v1/purchase-orders/{po_id}/approve",
        )

        auth_as(technician_user)
        resp = client.post(
            f"/api/v1/purchase-orders/{po_id}/mark-ordered",
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["status"] == "ORDERED"


class TestCancelPO:
    def test_cancel_with_reason(
        self, client, auth_as, technician_user, department,
    ):
        auth_as(technician_user)
        create_resp = client.post(
            "/api/v1/purchase-orders",
            json=_po_payload(department.id),
        )
        po_id = create_resp.json()["data"]["id"]

        resp = client.post(
            f"/api/v1/purchase-orders/{po_id}/cancel",
            json={"reason": "No longer needed"},
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["status"] == "CANCELLED"
        assert data["cancellation_reason"] == "No longer needed"


class TestInvalidTransitions:
    def test_submit_already_submitted_returns_409(
        self, client, auth_as, technician_user, department,
    ):
        auth_as(technician_user)
        create_resp = client.post(
            "/api/v1/purchase-orders",
            json=_po_payload(department.id),
        )
        po_id = create_resp.json()["data"]["id"]
        client.post(
            f"/api/v1/purchase-orders/{po_id}/submit",
        )

        resp = client.post(
            f"/api/v1/purchase-orders/{po_id}/submit",
        )
        assert resp.status_code == 409


class TestTenantIsolation:
    def test_cannot_see_other_company_po(
        self, client, auth_as, technician_user,
        department, db_session, make_user,
    ):
        from src.auth_bc.user.domain.enums import UserRole
        from src.company_bc.company.domain.entities import Company
        from src.company_bc.company.infrastructure.repository import (
            CompanyRepository,
        )

        auth_as(technician_user)
        create_resp = client.post(
            "/api/v1/purchase-orders",
            json=_po_payload(department.id),
        )
        po_id = create_resp.json()["data"]["id"]

        other_company = Company.create(
            name="Other Co", email_domains=["other.com"],
        )
        co_repo = CompanyRepository(db_session)
        co_repo.save(other_company)
        co_repo.save_domains(
            other_company.id, other_company.email_domains,
        )
        db_session.flush()
        other_tech = make_user(
            "tech@other.com",
            role=UserRole.TECHNICIAN,
            company_id=other_company.id,
        )

        auth_as(other_tech)
        resp = client.get(
            f"/api/v1/purchase-orders/{po_id}",
        )
        assert resp.status_code == 404


class TestApproveWithBudgetEnforcement:
    def _create_and_submit_po(
        self, client, auth_as, technician_user, department,
    ):
        auth_as(technician_user)
        create_resp = client.post(
            "/api/v1/purchase-orders",
            json=_po_payload(department.id),
        )
        po_id = create_resp.json()["data"]["id"]
        client.post(
            f"/api/v1/purchase-orders/{po_id}/submit",
        )
        return po_id

    def test_approve_over_budget_strict_returns_409(
        self, client, auth_as, admin_user,
        technician_user, department, db_session,
    ):
        from src.procurement_bc.budget.domain.entities import (
            CompanyProcurementConfig,
            DepartmentBudget,
        )
        from src.procurement_bc.budget.infrastructure.repository import (
            CompanyProcurementConfigRepository,
            DepartmentBudgetRepository,
        )

        config = CompanyProcurementConfig.create(
            company_id=admin_user.company_id,
            enforcement_mode="strict",
            fiscal_year_start_month=1,
        )
        CompanyProcurementConfigRepository(db_session).save(config)
        budget = DepartmentBudget.create(
            company_id=admin_user.company_id,
            department_id=department.id,
            fiscal_year=2026,
            allocated_amount_cents=50000,
        )
        DepartmentBudgetRepository(db_session).save(budget)
        db_session.flush()

        po_id = self._create_and_submit_po(
            client, auth_as, technician_user, department,
        )

        auth_as(admin_user)
        resp = client.post(
            f"/api/v1/purchase-orders/{po_id}/approve",
        )

        assert resp.status_code == 409

    def test_approve_over_budget_warn_returns_200_with_warning(
        self, client, auth_as, admin_user,
        technician_user, department, db_session,
    ):
        from src.procurement_bc.budget.domain.entities import (
            CompanyProcurementConfig,
            DepartmentBudget,
        )
        from src.procurement_bc.budget.infrastructure.repository import (
            CompanyProcurementConfigRepository,
            DepartmentBudgetRepository,
        )

        config = CompanyProcurementConfig.create(
            company_id=admin_user.company_id,
            enforcement_mode="warn",
            fiscal_year_start_month=1,
        )
        CompanyProcurementConfigRepository(db_session).save(config)
        budget = DepartmentBudget.create(
            company_id=admin_user.company_id,
            department_id=department.id,
            fiscal_year=2026,
            allocated_amount_cents=50000,
        )
        DepartmentBudgetRepository(db_session).save(budget)
        db_session.flush()

        po_id = self._create_and_submit_po(
            client, auth_as, technician_user, department,
        )

        auth_as(admin_user)
        resp = client.post(
            f"/api/v1/purchase-orders/{po_id}/approve",
        )

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["status"] == "APPROVED"
        assert "budget_warning" in data


class TestReceiveItems:
    def _create_ordered_po(
        self, client, auth_as, technician_user,
        admin_user, department,
    ):
        auth_as(technician_user)
        create_resp = client.post(
            "/api/v1/purchase-orders",
            json=_po_payload(department.id),
        )
        po_id = create_resp.json()["data"]["id"]
        item_id = create_resp.json()["data"]["items"][0]["id"]
        client.post(
            f"/api/v1/purchase-orders/{po_id}/submit",
        )
        auth_as(admin_user)
        client.post(
            f"/api/v1/purchase-orders/{po_id}/approve",
        )
        auth_as(technician_user)
        client.post(
            f"/api/v1/purchase-orders/{po_id}/mark-ordered",
        )
        return po_id, item_id

    def test_partial_receipt(
        self, client, auth_as, technician_user,
        admin_user, department,
    ):
        po_id, item_id = self._create_ordered_po(
            client, auth_as, technician_user,
            admin_user, department,
        )

        auth_as(technician_user)
        resp = client.post(
            f"/api/v1/purchase-orders/{po_id}/receive",
            json={
                "items": [{
                    "item_id": item_id,
                    "received_quantity": 1,
                }],
            },
        )

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["status"] == "PARTIALLY_RECEIVED"
        assert data["items"][0]["received_quantity"] == 1

    def test_full_receipt(
        self, client, auth_as, technician_user,
        admin_user, department,
    ):
        po_id, item_id = self._create_ordered_po(
            client, auth_as, technician_user,
            admin_user, department,
        )

        auth_as(technician_user)
        resp = client.post(
            f"/api/v1/purchase-orders/{po_id}/receive",
            json={
                "items": [{
                    "item_id": item_id,
                    "received_quantity": 2,
                }],
            },
        )

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["status"] == "RECEIVED"
        assert data["items"][0]["received_quantity"] == 2

    def test_receive_with_asset_creation(
        self, client, auth_as, technician_user,
        admin_user, department,
    ):
        po_id, item_id = self._create_ordered_po(
            client, auth_as, technician_user,
            admin_user, department,
        )

        auth_as(technician_user)
        resp = client.post(
            f"/api/v1/purchase-orders/{po_id}/receive",
            json={
                "items": [{
                    "item_id": item_id,
                    "received_quantity": 1,
                    "create_asset": True,
                }],
            },
        )

        assert resp.status_code == 200
        data = resp.json()["data"]
        item = data["items"][0]
        assert item["linked_asset_id"] is not None

    def test_over_receive_returns_422(
        self, client, auth_as, technician_user,
        admin_user, department,
    ):
        po_id, item_id = self._create_ordered_po(
            client, auth_as, technician_user,
            admin_user, department,
        )

        auth_as(technician_user)
        resp = client.post(
            f"/api/v1/purchase-orders/{po_id}/receive",
            json={
                "items": [{
                    "item_id": item_id,
                    "received_quantity": 10,
                }],
            },
        )

        assert resp.status_code == 422

    def test_receive_wrong_status_returns_409(
        self, client, auth_as, technician_user,
        department,
    ):
        auth_as(technician_user)
        create_resp = client.post(
            "/api/v1/purchase-orders",
            json=_po_payload(department.id),
        )
        po_id = create_resp.json()["data"]["id"]
        item_id = create_resp.json()["data"]["items"][0]["id"]

        resp = client.post(
            f"/api/v1/purchase-orders/{po_id}/receive",
            json={
                "items": [{
                    "item_id": item_id,
                    "received_quantity": 1,
                }],
            },
        )

        assert resp.status_code == 409


class TestClosePO:
    def test_close_received_po(
        self, client, auth_as, technician_user,
        admin_user, department,
    ):
        auth_as(technician_user)
        create_resp = client.post(
            "/api/v1/purchase-orders",
            json=_po_payload(department.id),
        )
        po_id = create_resp.json()["data"]["id"]
        item_id = create_resp.json()["data"]["items"][0]["id"]
        client.post(
            f"/api/v1/purchase-orders/{po_id}/submit",
        )
        auth_as(admin_user)
        client.post(
            f"/api/v1/purchase-orders/{po_id}/approve",
        )
        auth_as(technician_user)
        client.post(
            f"/api/v1/purchase-orders/{po_id}/mark-ordered",
        )
        client.post(
            f"/api/v1/purchase-orders/{po_id}/receive",
            json={
                "items": [{
                    "item_id": item_id,
                    "received_quantity": 2,
                }],
            },
        )

        resp = client.post(
            f"/api/v1/purchase-orders/{po_id}/close",
        )

        assert resp.status_code == 200
        assert resp.json()["data"]["status"] == "CLOSED"


class TestPOPdf:
    def _create_approved_po(self, client, auth_as, technician_user, admin_user, department):
        auth_as(technician_user)
        resp = client.post(
            "/api/v1/purchase-orders",
            json=_po_payload(department.id),
        )
        po_id = resp.json()["data"]["id"]
        client.post(f"/api/v1/purchase-orders/{po_id}/submit")

        auth_as(admin_user)
        client.post(f"/api/v1/purchase-orders/{po_id}/approve")

        auth_as(technician_user)
        return po_id

    def test_generate_pdf_approved_po(
        self, client, auth_as, technician_user, admin_user, department,
    ):
        po_id = self._create_approved_po(
            client, auth_as, technician_user, admin_user, department,
        )

        resp = client.post(f"/api/v1/purchase-orders/{po_id}/pdf")

        assert resp.status_code == 200
        assert resp.json()["data"]["status"] == "generating"

    def test_generate_pdf_draft_po_fails(
        self, client, auth_as, technician_user, department,
    ):
        auth_as(technician_user)
        resp = client.post(
            "/api/v1/purchase-orders",
            json=_po_payload(department.id),
        )
        po_id = resp.json()["data"]["id"]

        resp = client.post(f"/api/v1/purchase-orders/{po_id}/pdf")

        assert resp.status_code == 409

    def test_get_pdf_not_generated_yet(
        self, client, auth_as, technician_user, admin_user, department,
    ):
        po_id = self._create_approved_po(
            client, auth_as, technician_user, admin_user, department,
        )

        resp = client.get(f"/api/v1/purchase-orders/{po_id}/pdf")

        assert resp.status_code == 404
