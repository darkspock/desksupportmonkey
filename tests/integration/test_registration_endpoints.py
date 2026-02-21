"""Integration tests for /api/v1/register endpoints (public)."""

import pytest
from unittest.mock import patch, MagicMock


class TestRegisterCompany:
    @patch("core.email.get_email_service")
    def test_register_company(self, mock_email, client):
        mock_email.return_value = MagicMock()

        resp = client.post("/api/v1/register", json={
            "name": "New Startup",
            "admin_email": "founder@newstartup.com",
            "email_domains": ["newstartup.com"],
        })

        assert resp.status_code == 201
        assert "registered" in resp.json()["data"]["message"].lower()

    @patch("core.email.get_email_service")
    def test_register_duplicate_name(self, mock_email, client, company):
        mock_email.return_value = MagicMock()

        resp = client.post("/api/v1/register", json={
            "name": company.name,
            "admin_email": "admin@dupname.com",
            "email_domains": ["dupname.com"],
        })

        assert resp.status_code == 409

    @patch("core.email.get_email_service")
    def test_register_duplicate_domain(self, mock_email, client, company):
        mock_email.return_value = MagicMock()

        resp = client.post("/api/v1/register", json={
            "name": "Other Company",
            "admin_email": "admin@testco.com",
            "email_domains": ["testco.com"],  # already taken
        })

        assert resp.status_code == 409

    @patch("core.email.get_email_service")
    def test_register_duplicate_admin_email(self, mock_email, client, admin_user, company):
        mock_email.return_value = MagicMock()

        resp = client.post("/api/v1/register", json={
            "name": "Another Corp",
            "admin_email": admin_user.email,
            "email_domains": ["anothercorp.com"],
        })

        assert resp.status_code == 409

    @patch("core.email.get_email_service")
    def test_register_accepts_leading_at_in_email_domain(self, mock_email, client):
        mock_email.return_value = MagicMock()

        resp = client.post("/api/v1/register", json={
            "name": "At Domain Startup",
            "admin_email": "founder@atdomain.tech",
            "email_domains": ["@atdomain.tech"],
        })

        assert resp.status_code == 201
        assert "registered" in resp.json()["data"]["message"].lower()
