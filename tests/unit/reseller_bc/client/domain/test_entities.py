from datetime import timedelta

import pytest

from src.reseller_bc.client.domain.entities import ResellerClient
from src.reseller_bc.client.domain.enums import ClientSource


class TestResellerClientCreate:
    def test_create_demo_sets_expiry(self):
        client = ResellerClient.create(
            reseller_id="res-1",
            company_id="comp-1",
            source=ClientSource.MANUAL,
            is_demo=True,
        )
        assert client.is_demo is True
        assert client.demo_expires_at is not None
        # Should be roughly 14 days from now
        diff = client.demo_expires_at - client.created_at
        assert timedelta(days=13, hours=23) < diff < timedelta(days=14, hours=1)

    def test_create_non_demo_no_expiry(self):
        client = ResellerClient.create(
            reseller_id="res-1",
            company_id="comp-1",
            source=ClientSource.MANUAL,
            is_demo=False,
        )
        assert client.is_demo is False
        assert client.demo_expires_at is None

    def test_create_with_explicit_id(self):
        client = ResellerClient.create(
            reseller_id="res-1",
            company_id="comp-1",
            source=ClientSource.MANUAL,
            id="custom-id-123",
        )
        assert client.id == "custom-id-123"

    def test_create_auto_generates_ulid(self):
        client = ResellerClient.create(
            reseller_id="res-1",
            company_id="comp-1",
            source=ClientSource.MANUAL,
        )
        assert client.id is not None
        assert len(client.id) == 26  # ULID length

    def test_create_preserves_source_manual(self):
        client = ResellerClient.create(
            reseller_id="res-1",
            company_id="comp-1",
            source=ClientSource.MANUAL,
        )
        assert client.source == ClientSource.MANUAL

    def test_create_preserves_source_referral(self):
        client = ResellerClient.create(
            reseller_id="res-1",
            company_id="comp-1",
            source=ClientSource.REFERRAL,
        )
        assert client.source == ClientSource.REFERRAL

    def test_create_sets_created_at(self):
        client = ResellerClient.create(
            reseller_id="res-1",
            company_id="comp-1",
            source=ClientSource.MANUAL,
        )
        assert client.created_at is not None

    def test_create_preserves_reseller_and_company(self):
        client = ResellerClient.create(
            reseller_id="res-abc",
            company_id="comp-xyz",
            source=ClientSource.MANUAL,
        )
        assert client.reseller_id == "res-abc"
        assert client.company_id == "comp-xyz"
