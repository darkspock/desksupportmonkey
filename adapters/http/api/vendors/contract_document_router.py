import logging

import ulid
from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
    status,
)
from fastapi.responses import Response

from adapters.http.api.auth.dependencies import get_current_user
from adapters.http.api.vendors.contract_dependencies import (
    get_contract_document_repo,
    get_contract_repo,
    get_contract_storage,
)
from adapters.http.api.vendors.contract_document_schemas import (
    DocumentResponse,
)
from core.storage import StorageServiceInterface
from src.auth_bc.user.domain.entities import User
from src.auth_bc.user.domain.enums import UserRole
from src.procurement_bc.vendor.application.commands.soft_delete_contract_document import (  # noqa: E501
    SoftDeleteContractDocumentCommand,
    SoftDeleteContractDocumentCommandHandler,
)
from src.procurement_bc.vendor.application.commands.upload_contract_document import (  # noqa: E501
    UploadContractDocumentCommand,
    UploadContractDocumentCommandHandler,
)
from src.procurement_bc.vendor.application.queries.download_contract_document import (  # noqa: E501
    DownloadContractDocumentQuery,
    DownloadContractDocumentQueryHandler,
)
from src.procurement_bc.vendor.application.queries.list_contract_documents import (  # noqa: E501
    ListContractDocumentsQuery,
    ListContractDocumentsQueryHandler,
)
from src.procurement_bc.vendor.domain.entities import (
    VendorContractDocument,
)
from src.procurement_bc.vendor.domain.exceptions import (
    ContractDocumentNotFoundError,
    ContractNotFoundError,
)
from src.procurement_bc.vendor.infrastructure.repository import (
    VendorContractDocumentRepository,
    VendorContractRepository,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/vendors/{vendor_id}/contracts/{contract_id}/documents",
    tags=["vendor-contract-documents"],
)

MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB


def _to_response(doc: VendorContractDocument) -> DocumentResponse:
    return DocumentResponse(
        id=doc.id,
        contract_id=doc.contract_id,
        company_id=doc.company_id,
        filename=doc.filename,
        content_type=doc.content_type,
        size_bytes=doc.size_bytes,
        uploaded_by=doc.uploaded_by,
        created_at=doc.created_at,
    )


def _require_technician(user: User) -> None:
    if not user.role.has_access(UserRole.TECHNICIAN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Technician access required",
        )


def _require_admin(user: User) -> None:
    if not user.role.has_access(UserRole.ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )


@router.post("", status_code=status.HTTP_201_CREATED)
async def upload_document(
    vendor_id: str,
    contract_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    contract_repo: VendorContractRepository = Depends(
        get_contract_repo,
    ),
    document_repo: VendorContractDocumentRepository = Depends(
        get_contract_document_repo,
    ),
    storage: StorageServiceInterface = Depends(
        get_contract_storage,
    ),
):
    _require_admin(current_user)

    file_data = await file.read()
    if len(file_data) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File size exceeds 20 MB limit",
        )

    doc_id = str(ulid.new())
    handler = UploadContractDocumentCommandHandler(
        contract_repo=contract_repo,
        document_repo=document_repo,
        storage_service=storage,
    )
    try:
        handler.handle(
            UploadContractDocumentCommand(
                id=doc_id,
                contract_id=contract_id,
                vendor_id=vendor_id,
                company_id=current_user.company_id,
                filename=file.filename or "unnamed",
                content_type=file.content_type or "application/octet-stream",
                size_bytes=len(file_data),
                file_data=file_data,
                uploaded_by=current_user.id,
            )
        )
    except ContractNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contract not found",
        )

    document = document_repo.find_by_id(
        doc_id, contract_id, current_user.company_id,
    )
    return {
        "data": _to_response(document).model_dump(mode="json"),
    }


@router.get("")
def list_documents(
    vendor_id: str,
    contract_id: str,
    current_user: User = Depends(get_current_user),
    document_repo: VendorContractDocumentRepository = Depends(
        get_contract_document_repo,
    ),
):
    _require_technician(current_user)

    handler = ListContractDocumentsQueryHandler(
        document_repo=document_repo,
    )
    documents = handler.handle(
        ListContractDocumentsQuery(
            contract_id=contract_id,
            company_id=current_user.company_id,
        )
    )
    return {
        "data": [
            _to_response(d).model_dump(mode="json")
            for d in documents
        ],
    }


@router.get("/{document_id}/download")
def download_document(
    vendor_id: str,
    contract_id: str,
    document_id: str,
    current_user: User = Depends(get_current_user),
    document_repo: VendorContractDocumentRepository = Depends(
        get_contract_document_repo,
    ),
    storage: StorageServiceInterface = Depends(
        get_contract_storage,
    ),
):
    _require_technician(current_user)

    handler = DownloadContractDocumentQueryHandler(
        document_repo=document_repo,
        storage_service=storage,
    )
    try:
        result = handler.handle(
            DownloadContractDocumentQuery(
                document_id=document_id,
                contract_id=contract_id,
                company_id=current_user.company_id,
            )
        )
    except ContractDocumentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    return Response(
        content=result.data,
        media_type=result.content_type,
        headers={
            "Content-Disposition": f'attachment; filename="{result.filename}"',
        },
    )


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_document(
    vendor_id: str,
    contract_id: str,
    document_id: str,
    current_user: User = Depends(get_current_user),
    document_repo: VendorContractDocumentRepository = Depends(
        get_contract_document_repo,
    ),
):
    _require_admin(current_user)

    handler = SoftDeleteContractDocumentCommandHandler(
        document_repo=document_repo,
    )
    try:
        handler.handle(
            SoftDeleteContractDocumentCommand(
                document_id=document_id,
                contract_id=contract_id,
                company_id=current_user.company_id,
                performed_by=current_user.id,
            )
        )
    except ContractDocumentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
