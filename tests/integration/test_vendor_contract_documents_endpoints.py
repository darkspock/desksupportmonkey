"""Integration tests for vendor contract document endpoints."""
import io

import pytest


def _create_vendor_and_contract(client):
    """Create a vendor and a contract, return (vendor_id, contract_id)."""
    vendor_resp = client.post(
        "/api/v1/vendors",
        json={"name": "Doc Test Vendor"},
    )
    vendor_id = vendor_resp.json()["data"]["id"]

    contract_resp = client.post(
        f"/api/v1/vendors/{vendor_id}/contracts",
        json={
            "contract_type": "service",
            "title": "Doc Test Contract",
            "start_date": "2026-01-01",
        },
    )
    contract_id = contract_resp.json()["data"]["id"]
    return vendor_id, contract_id


class TestUploadDocument:
    def test_upload_document(
        self, client, auth_as, admin_user,
    ):
        auth_as(admin_user)
        vendor_id, contract_id = _create_vendor_and_contract(
            client,
        )

        resp = client.post(
            f"/api/v1/vendors/{vendor_id}/contracts"
            f"/{contract_id}/documents",
            files={
                "file": (
                    "contract.pdf",
                    io.BytesIO(b"fake pdf content"),
                    "application/pdf",
                ),
            },
        )

        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["filename"] == "contract.pdf"
        assert data["content_type"] == "application/pdf"
        assert data["size_bytes"] > 0

    def test_upload_contract_not_found(
        self, client, auth_as, admin_user,
    ):
        auth_as(admin_user)
        vendor_resp = client.post(
            "/api/v1/vendors",
            json={"name": "No Contract Vendor"},
        )
        vendor_id = vendor_resp.json()["data"]["id"]

        resp = client.post(
            f"/api/v1/vendors/{vendor_id}/contracts"
            "/nonexistent/documents",
            files={
                "file": (
                    "test.pdf",
                    io.BytesIO(b"data"),
                    "application/pdf",
                ),
            },
        )
        assert resp.status_code == 404


class TestListDocuments:
    def test_list_documents(
        self, client, auth_as, admin_user,
    ):
        auth_as(admin_user)
        vendor_id, contract_id = _create_vendor_and_contract(
            client,
        )

        # Upload two documents
        for name in ["doc1.pdf", "doc2.pdf"]:
            client.post(
                f"/api/v1/vendors/{vendor_id}/contracts"
                f"/{contract_id}/documents",
                files={
                    "file": (
                        name,
                        io.BytesIO(b"content"),
                        "application/pdf",
                    ),
                },
            )

        resp = client.get(
            f"/api/v1/vendors/{vendor_id}/contracts"
            f"/{contract_id}/documents",
        )

        assert resp.status_code == 200
        assert len(resp.json()["data"]) >= 2

    def test_technician_can_list(
        self, client, auth_as, admin_user, technician_user,
    ):
        auth_as(admin_user)
        vendor_id, contract_id = _create_vendor_and_contract(
            client,
        )

        auth_as(technician_user)
        resp = client.get(
            f"/api/v1/vendors/{vendor_id}/contracts"
            f"/{contract_id}/documents",
        )
        assert resp.status_code == 200


class TestDownloadDocument:
    def test_download_document(
        self, client, auth_as, admin_user,
    ):
        auth_as(admin_user)
        vendor_id, contract_id = _create_vendor_and_contract(
            client,
        )

        upload_resp = client.post(
            f"/api/v1/vendors/{vendor_id}/contracts"
            f"/{contract_id}/documents",
            files={
                "file": (
                    "download_test.pdf",
                    io.BytesIO(b"downloadable content"),
                    "application/pdf",
                ),
            },
        )
        doc_id = upload_resp.json()["data"]["id"]

        resp = client.get(
            f"/api/v1/vendors/{vendor_id}/contracts"
            f"/{contract_id}/documents/{doc_id}/download",
        )

        assert resp.status_code == 200
        assert resp.content == b"downloadable content"
        assert "download_test.pdf" in resp.headers.get(
            "content-disposition", "",
        )

    def test_download_not_found(
        self, client, auth_as, admin_user,
    ):
        auth_as(admin_user)
        vendor_id, contract_id = _create_vendor_and_contract(
            client,
        )

        resp = client.get(
            f"/api/v1/vendors/{vendor_id}/contracts"
            f"/{contract_id}/documents/nonexistent/download",
        )
        assert resp.status_code == 404


class TestDeleteDocument:
    def test_soft_delete_document(
        self, client, auth_as, admin_user,
    ):
        auth_as(admin_user)
        vendor_id, contract_id = _create_vendor_and_contract(
            client,
        )

        upload_resp = client.post(
            f"/api/v1/vendors/{vendor_id}/contracts"
            f"/{contract_id}/documents",
            files={
                "file": (
                    "delete_me.pdf",
                    io.BytesIO(b"to be deleted"),
                    "application/pdf",
                ),
            },
        )
        doc_id = upload_resp.json()["data"]["id"]

        resp = client.delete(
            f"/api/v1/vendors/{vendor_id}/contracts"
            f"/{contract_id}/documents/{doc_id}",
        )

        assert resp.status_code == 204

        # Should not appear in list
        list_resp = client.get(
            f"/api/v1/vendors/{vendor_id}/contracts"
            f"/{contract_id}/documents",
        )
        ids = [d["id"] for d in list_resp.json()["data"]]
        assert doc_id not in ids


class TestDocumentPermissions:
    def test_employee_cannot_upload(
        self, client, auth_as, employee_user,
    ):
        auth_as(employee_user)
        resp = client.post(
            "/api/v1/vendors/v1/contracts/c1/documents",
            files={
                "file": (
                    "test.pdf",
                    io.BytesIO(b"data"),
                    "application/pdf",
                ),
            },
        )
        assert resp.status_code == 403

    def test_technician_cannot_upload(
        self, client, auth_as, technician_user, admin_user,
    ):
        auth_as(admin_user)
        vendor_id, contract_id = _create_vendor_and_contract(
            client,
        )

        auth_as(technician_user)
        resp = client.post(
            f"/api/v1/vendors/{vendor_id}/contracts"
            f"/{contract_id}/documents",
            files={
                "file": (
                    "test.pdf",
                    io.BytesIO(b"data"),
                    "application/pdf",
                ),
            },
        )
        assert resp.status_code == 403

    def test_technician_cannot_delete(
        self, client, auth_as, technician_user, admin_user,
    ):
        auth_as(admin_user)
        vendor_id, contract_id = _create_vendor_and_contract(
            client,
        )

        upload_resp = client.post(
            f"/api/v1/vendors/{vendor_id}/contracts"
            f"/{contract_id}/documents",
            files={
                "file": (
                    "test.pdf",
                    io.BytesIO(b"data"),
                    "application/pdf",
                ),
            },
        )
        doc_id = upload_resp.json()["data"]["id"]

        auth_as(technician_user)
        resp = client.delete(
            f"/api/v1/vendors/{vendor_id}/contracts"
            f"/{contract_id}/documents/{doc_id}",
        )
        assert resp.status_code == 403
