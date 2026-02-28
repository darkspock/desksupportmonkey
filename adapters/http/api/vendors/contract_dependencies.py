from fastapi import Depends
from sqlalchemy.orm import Session

from core.database import get_db
from core.storage import S3StorageService, StorageServiceInterface
from src.procurement_bc.vendor.infrastructure.repository import (
    VendorContractRepository,
    VendorContractDocumentRepository,
)


def get_contract_repo(
    db: Session = Depends(get_db),
) -> VendorContractRepository:
    return VendorContractRepository(db)


def get_contract_document_repo(
    db: Session = Depends(get_db),
) -> VendorContractDocumentRepository:
    return VendorContractDocumentRepository(db)


def get_contract_storage() -> StorageServiceInterface:
    return S3StorageService(bucket="vendor-contracts")
