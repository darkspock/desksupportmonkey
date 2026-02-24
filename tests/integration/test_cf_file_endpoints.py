"""Integration tests for custom field file upload/download endpoints."""
import io
from unittest.mock import MagicMock, patch

from sqlalchemy import update

from src.company_bc.company.infrastructure.models import CompanyModel


def _make_enterprise(db_session, company):
    """Set company to Enterprise plan."""
    db_session.execute(
        update(CompanyModel)
        .where(CompanyModel.id == company.id)
        .values(plan="enterprise", billing_status="active")
    )
    db_session.flush()


UPLOAD_URL = "/api/v1/custom-fields/files/upload"
DOWNLOAD_URL = "/api/v1/custom-fields/files/{file_id}/download"


class TestFileUpload:

    @patch("adapters.http.api.custom_fields.routers.S3StorageService")
    def test_upload_valid_pdf(
        self, mock_storage_cls, client, db_session, admin_user, auth_as, company
    ):
        _make_enterprise(db_session, company)
        auth_as(admin_user)

        mock_storage = MagicMock()
        mock_storage_cls.return_value = mock_storage

        pdf_content = b"%PDF-1.4 test content"
        resp = client.post(
            f"{UPLOAD_URL}?entity_type=asset&field_key=attachments",
            files={"file": ("report.pdf", io.BytesIO(pdf_content), "application/pdf")},
        )

        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["name"] == "report.pdf"
        assert data["size"] == len(pdf_content)
        assert data["mime"] == "application/pdf"
        assert data["key"].startswith("cf-files/")
        assert data["key"].endswith(".pdf")
        assert "id" in data
        mock_storage.upload.assert_called_once()

    @patch("adapters.http.api.custom_fields.routers.S3StorageService")
    def test_upload_valid_image(
        self, mock_storage_cls, client, db_session, admin_user, auth_as, company
    ):
        _make_enterprise(db_session, company)
        auth_as(admin_user)
        mock_storage_cls.return_value = MagicMock()

        resp = client.post(
            f"{UPLOAD_URL}?entity_type=asset&field_key=photos",
            files={"file": ("photo.png", io.BytesIO(b"\x89PNG"), "image/png")},
        )
        assert resp.status_code == 201
        assert resp.json()["data"]["mime"] == "image/png"

    def test_upload_rejects_disallowed_mime(
        self, client, db_session, admin_user, auth_as, company
    ):
        _make_enterprise(db_session, company)
        auth_as(admin_user)

        resp = client.post(
            f"{UPLOAD_URL}?entity_type=asset&field_key=attachments",
            files={"file": ("script.exe", io.BytesIO(b"MZ"), "application/x-msdownload")},
        )
        assert resp.status_code == 422

    def test_upload_rejects_disallowed_extension(
        self, client, db_session, admin_user, auth_as, company
    ):
        _make_enterprise(db_session, company)
        auth_as(admin_user)

        resp = client.post(
            f"{UPLOAD_URL}?entity_type=asset&field_key=attachments",
            files={"file": ("script.sh", io.BytesIO(b"#!/bin/bash"), "application/pdf")},
        )
        assert resp.status_code == 422

    @patch("adapters.http.api.custom_fields.routers.S3StorageService")
    def test_upload_rejects_oversized(
        self, mock_storage_cls, client, db_session, admin_user, auth_as, company
    ):
        _make_enterprise(db_session, company)
        auth_as(admin_user)

        big_content = b"x" * (10 * 1024 * 1024 + 1)
        resp = client.post(
            f"{UPLOAD_URL}?entity_type=asset&field_key=attachments",
            files={"file": ("big.pdf", io.BytesIO(big_content), "application/pdf")},
        )
        assert resp.status_code == 422
        assert "maximum size" in resp.json()["detail"].lower()


class TestFileDownload:

    @patch("adapters.http.api.custom_fields.routers.S3StorageService")
    def test_download_returns_signed_url(
        self, mock_storage_cls, client, db_session, admin_user, auth_as, company
    ):
        _make_enterprise(db_session, company)
        auth_as(admin_user)

        mock_storage = MagicMock()
        mock_storage.get_signed_url.return_value = "https://s3.example.com/signed"
        mock_storage_cls.return_value = mock_storage

        key = f"cf-files/{company.id}/asset/attachments/ulid1.pdf"
        resp = client.get(
            f"/api/v1/custom-fields/files/ulid1/download",
            params={"key": key},
        )

        assert resp.status_code == 200
        assert resp.json()["data"]["url"] == "https://s3.example.com/signed"
        mock_storage.get_signed_url.assert_called_once_with(key, expiration=3600)

    @patch("adapters.http.api.custom_fields.routers.S3StorageService")
    def test_download_rejects_cross_company(
        self, mock_storage_cls, client, db_session, admin_user, auth_as, company
    ):
        _make_enterprise(db_session, company)
        auth_as(admin_user)

        # Key belongs to a different company
        key = "cf-files/other-company-id/asset/attachments/ulid1.pdf"
        resp = client.get(
            f"/api/v1/custom-fields/files/ulid1/download",
            params={"key": key},
        )

        assert resp.status_code == 403
        assert "access denied" in resp.json()["detail"].lower()
