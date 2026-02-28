import pytest
from datetime import date
from unittest.mock import MagicMock

from src.procurement_bc.vendor.application.queries.list_contracts import (
    ListContractsQuery,
    ListContractsQueryHandler,
)
from src.procurement_bc.vendor.application.queries.get_contract import (
    GetContractQuery,
    GetContractQueryHandler,
    ContractDetailResult,
)
from src.procurement_bc.vendor.application.queries.list_contract_documents import (
    ListContractDocumentsQuery,
    ListContractDocumentsQueryHandler,
)
from src.procurement_bc.vendor.application.queries.download_contract_document import (
    DownloadContractDocumentQuery,
    DownloadContractDocumentQueryHandler,
)
from src.procurement_bc.vendor.domain.entities import (
    VendorContract,
    VendorContractDocument,
)
from src.procurement_bc.vendor.domain.enums import (
    ContractStatus,
    ContractType,
)
from src.procurement_bc.vendor.domain.exceptions import (
    ContractDocumentNotFoundError,
    ContractNotFoundError,
)


class TestListContractsQueryHandler:
    def setup_method(self):
        self.contract_repo = MagicMock()
        self.handler = ListContractsQueryHandler(
            contract_repo=self.contract_repo,
        )

    def test_returns_paginated_list(self):
        contracts = [
            VendorContract.create(
                vendor_id="v1",
                company_id="comp1",
                contract_type=ContractType.SERVICE,
                title=f"Contract {i}",
                start_date=date(2026, 1, 1),
            )
            for i in range(3)
        ]
        self.contract_repo.find_all_by_vendor.return_value = (
            contracts, 3,
        )
        result, total = self.handler.handle(
            ListContractsQuery(
                vendor_id="v1",
                company_id="comp1",
                page=1,
                page_size=20,
            )
        )
        assert len(result) == 3
        assert total == 3

    def test_filters_by_status(self):
        self.contract_repo.find_all_by_vendor.return_value = (
            [], 0,
        )
        self.handler.handle(
            ListContractsQuery(
                vendor_id="v1",
                company_id="comp1",
                status="active",
            )
        )
        call_kwargs = (
            self.contract_repo.find_all_by_vendor.call_args
        )
        assert call_kwargs.kwargs["status"] == ContractStatus.ACTIVE


class TestGetContractQueryHandler:
    def setup_method(self):
        self.contract_repo = MagicMock()
        self.document_repo = MagicMock()
        self.handler = GetContractQueryHandler(
            contract_repo=self.contract_repo,
            document_repo=self.document_repo,
        )

    def test_returns_contract_with_doc_count(self):
        contract = VendorContract.create(
            vendor_id="v1",
            company_id="comp1",
            contract_type=ContractType.SAAS,
            title="Test",
            start_date=date(2026, 1, 1),
        )
        self.contract_repo.find_by_id.return_value = contract
        self.document_repo.count_by_contract.return_value = 3
        result = self.handler.handle(
            GetContractQuery(
                contract_id=contract.id,
                vendor_id="v1",
                company_id="comp1",
            )
        )
        assert isinstance(result, ContractDetailResult)
        assert result.contract == contract
        assert result.document_count == 3

    def test_not_found_raises(self):
        self.contract_repo.find_by_id.return_value = None
        with pytest.raises(ContractNotFoundError):
            self.handler.handle(
                GetContractQuery(
                    contract_id="c1",
                    vendor_id="v1",
                    company_id="comp1",
                )
            )


class TestListContractDocumentsQueryHandler:
    def setup_method(self):
        self.document_repo = MagicMock()
        self.handler = ListContractDocumentsQueryHandler(
            document_repo=self.document_repo,
        )

    def test_returns_documents(self):
        docs = [MagicMock(), MagicMock()]
        self.document_repo.find_all_by_contract.return_value = docs
        result = self.handler.handle(
            ListContractDocumentsQuery(
                contract_id="c1",
                company_id="comp1",
            )
        )
        assert len(result) == 2


class TestDownloadContractDocumentQueryHandler:
    def setup_method(self):
        self.document_repo = MagicMock()
        self.storage = MagicMock()
        self.handler = DownloadContractDocumentQueryHandler(
            document_repo=self.document_repo,
            storage_service=self.storage,
        )

    def test_downloads_document(self):
        doc = MagicMock()
        doc.storage_key = "comp1/v1/c1/d1/file.pdf"
        doc.filename = "file.pdf"
        doc.content_type = "application/pdf"
        self.document_repo.find_by_id.return_value = doc
        self.storage.download.return_value = b"pdf data"
        result = self.handler.handle(
            DownloadContractDocumentQuery(
                document_id="d1",
                contract_id="c1",
                company_id="comp1",
            )
        )
        assert result.data == b"pdf data"
        assert result.filename == "file.pdf"
        assert result.content_type == "application/pdf"

    def test_not_found_raises(self):
        self.document_repo.find_by_id.return_value = None
        with pytest.raises(ContractDocumentNotFoundError):
            self.handler.handle(
                DownloadContractDocumentQuery(
                    document_id="d1",
                    contract_id="c1",
                    company_id="comp1",
                )
            )
