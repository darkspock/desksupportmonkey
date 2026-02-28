import pytest
from unittest.mock import MagicMock

from src.procurement_bc.vendor.application.commands.upload_contract_document import (
    UploadContractDocumentCommand,
    UploadContractDocumentCommandHandler,
)
from src.procurement_bc.vendor.application.commands.soft_delete_contract_document import (
    SoftDeleteContractDocumentCommand,
    SoftDeleteContractDocumentCommandHandler,
)
from src.procurement_bc.vendor.domain.entities import VendorContractDocument
from src.procurement_bc.vendor.domain.exceptions import (
    ContractDocumentNotFoundError,
    ContractNotFoundError,
)


class TestUploadContractDocumentCommandHandler:
    def setup_method(self):
        self.contract_repo = MagicMock()
        self.document_repo = MagicMock()
        self.storage = MagicMock()
        self.handler = UploadContractDocumentCommandHandler(
            contract_repo=self.contract_repo,
            document_repo=self.document_repo,
            storage_service=self.storage,
        )

    def test_uploads_document(self):
        self.contract_repo.find_by_id.return_value = MagicMock()
        self.handler.handle(
            UploadContractDocumentCommand(
                contract_id="c1",
                vendor_id="v1",
                company_id="comp1",
                filename="contract.pdf",
                content_type="application/pdf",
                size_bytes=1024,
                file_data=b"fake pdf data",
                uploaded_by="user1",
            )
        )
        self.storage.ensure_bucket.assert_called_once()
        self.storage.upload.assert_called_once()
        self.document_repo.save.assert_called_once()
        saved = self.document_repo.save.call_args[0][0]
        assert isinstance(saved, VendorContractDocument)
        assert saved.filename == "contract.pdf"
        assert "comp1" in saved.storage_key
        assert "v1" in saved.storage_key

    def test_contract_not_found(self):
        self.contract_repo.find_by_id.return_value = None
        with pytest.raises(ContractNotFoundError):
            self.handler.handle(
                UploadContractDocumentCommand(
                    contract_id="c1",
                    vendor_id="v1",
                    company_id="comp1",
                    filename="test.pdf",
                    content_type="application/pdf",
                    size_bytes=100,
                    file_data=b"data",
                    uploaded_by="user1",
                )
            )
        self.storage.upload.assert_not_called()


class TestSoftDeleteContractDocumentCommandHandler:
    def setup_method(self):
        self.document_repo = MagicMock()
        self.handler = SoftDeleteContractDocumentCommandHandler(
            document_repo=self.document_repo,
        )

    def test_soft_deletes(self):
        self.document_repo.find_by_id.return_value = MagicMock()
        self.handler.handle(
            SoftDeleteContractDocumentCommand(
                document_id="d1",
                contract_id="c1",
                company_id="comp1",
                performed_by="user1",
            )
        )
        self.document_repo.soft_delete.assert_called_once()

    def test_not_found_raises(self):
        self.document_repo.find_by_id.return_value = None
        with pytest.raises(ContractDocumentNotFoundError):
            self.handler.handle(
                SoftDeleteContractDocumentCommand(
                    document_id="d1",
                    contract_id="c1",
                    company_id="comp1",
                    performed_by="user1",
                )
            )
