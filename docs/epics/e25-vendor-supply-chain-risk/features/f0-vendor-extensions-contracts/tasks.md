# Tasks: F0 — Vendor Extensions & Contracts

**Feature:** [requirements.md](../../requirements.md)
**Date:** 2026-02-26

## Summary

| # | Task | Complexity | Phase |
|---|------|-----------|-------|
| 1 | Domain: enums, extended Vendor entity, VendorContract entity, VendorContractDocument entity, exceptions, repository interfaces | L | Domain |
| 2 | Infrastructure: ORM models (VendorContractModel, VendorContractDocumentModel, extend VendorModel) | M | Infra |
| 3 | Infrastructure: Alembic migration | S | Infra |
| 4 | Infrastructure: VendorContract repository implementation | M | Infra |
| 5 | Infrastructure: VendorContractDocument repository + MinIO storage | M | Infra |
| 6 | Application: CreateContractCommand + handler | S | App |
| 7 | Application: UpdateContractCommand + handler | S | App |
| 8 | Application: ChangeContractStatusCommand + handler | S | App |
| 9 | Application: SoftDeleteContractCommand + handler | S | App |
| 10 | Application: ListContractsQuery + handler | S | App |
| 11 | Application: GetContractQuery + handler | S | App |
| 12 | Application: UploadContractDocumentCommand + handler | S | App |
| 13 | Application: ListContractDocumentsQuery + handler | S | App |
| 14 | Application: DownloadContractDocumentQuery + handler | S | App |
| 15 | Application: SoftDeleteContractDocumentCommand + handler | S | App |
| 16 | Application: UpdateVendorCommand extension (category, website, is_critical_ict) | S | App |
| 17 | Application: Contract auto-expiry Celery task | S | App |
| 18 | HTTP: contract schemas (request + response) | M | HTTP |
| 19 | HTTP: contract document schemas | S | HTTP |
| 20 | HTTP: contract router + dependencies | M | HTTP |
| 21 | HTTP: contract document router | M | HTTP |
| 22 | HTTP: Register routers in app.py | S | HTTP |
| 23 | Unit tests: domain entities (VendorContract state machine, VendorContractDocument) | M | Test |
| 24 | Unit tests: contract command handlers | M | Test |
| 25 | Unit tests: contract document command/query handlers | S | Test |
| 26 | Unit tests: contract query handlers | S | Test |
| 27 | Integration tests: contract endpoints | L | Test |
| 28 | Integration tests: contract document endpoints | M | Test |
| 29 | Frontend: TypeScript types (VendorContract, VendorContractDocument, extended Vendor) | S | FE |
| 30 | Frontend: Update VendorListPage with category badge, risk_level badge, link to detail | M | FE |
| 31 | Frontend: i18n EN/ES translations for contracts | S | FE |

## Detailed Tasks

### Phase 1: Domain

#### Task 1: Enums, entities, exceptions, repository interfaces
- **Files:**
  - `src/procurement_bc/vendor/domain/enums.py` (extend)
  - `src/procurement_bc/vendor/domain/entities.py` (extend Vendor + new VendorContract, VendorContractDocument)
  - `src/procurement_bc/vendor/domain/exceptions.py` (extend)
  - `src/procurement_bc/vendor/domain/repository.py` (extend with contract + document repo interfaces)
- **What:**
  - New enums: `ContractType` (service, supply, licensing, saas), `ContractStatus` (draft, active, expired, terminated), `VendorCategory` (hardware, software, saas, consulting, telecom, cloud, managed_services, other), `VendorRiskLevel` (low, medium, high, critical), `BusinessFunction` (it_operations, security, communications, data_storage, cloud_infrastructure, software, hardware_supply, consulting, other)
  - `VALID_CONTRACT_TRANSITIONS` dict: draft→[active, terminated], active→[expired, terminated], expired→[active], terminated→[draft]
  - Extend `Vendor` entity: add `is_critical_ict`, `risk_level`, `website`, `category` fields + `update_extended_fields()` method
  - `VendorContract` entity with `create()` factory, `change_status()` with transition validation, `update()`, `soft_delete()`
  - `VendorContractDocument` entity with `create()` factory, `soft_delete()`
  - Security clauses default dict constant `DEFAULT_SECURITY_CLAUSES`
  - New exceptions: `ContractNotFoundError`, `InvalidContractTransitionError`, `ContractDocumentNotFoundError`
  - `VendorContractRepositoryInterface` ABC: save, find_by_id, find_all_by_vendor, soft_delete, find_expired_active_contracts
  - `VendorContractDocumentRepositoryInterface` ABC: save, find_by_id, find_all_by_contract, soft_delete
- **Acceptance:** All domain types defined, VendorContract.change_status() validates transitions
- [x] Done

### Phase 2: Infrastructure

#### Task 2: ORM models
- **Files:**
  - `src/procurement_bc/vendor/infrastructure/models.py` (extend VendorModel + new models)
- **What:**
  - Extend `VendorModel`: add `is_critical_ict` (Bool, default false), `risk_level` (String nullable), `website` (String 500 nullable), `category` (String nullable)
  - `VendorContractModel`: all fields from entity spec, JSONB for security_clauses, `is_deleted` default false, indexes on (vendor_id, company_id), (company_id, status)
  - `VendorContractDocumentModel`: all fields from entity spec, `is_deleted` default false, index on (contract_id, company_id)
  - All use `Mapped[type]` annotations (SQLAlchemy 2.0 style)
- **Deps:** Task 1
- **Acceptance:** All models defined with proper indexes, foreign keys
- [x] Done

#### Task 3: Alembic migration
- **File:** `alembic/versions/` (new migration)
- **What:** Add columns to `vendors` table (is_critical_ict, risk_level, website, category). Create `vendor_contracts` table. Create `vendor_contract_documents` table. All with indexes.
- **Deps:** Task 2
- **Acceptance:** Migration runs up and down cleanly
- [x] Done

#### Task 4: VendorContract repository implementation
- **File:** `src/procurement_bc/vendor/infrastructure/repository.py` (extend or new file)
- **What:** Implement `VendorContractRepositoryInterface`: save (upsert), find_by_id (filter is_deleted=false), find_all_by_vendor (paginated, filter is_deleted=false), soft_delete, find_expired_active_contracts (status=active AND end_date < today AND is_deleted=false).
- **Deps:** Tasks 1-3
- **Acceptance:** All repo methods work, soft delete filters applied
- [x] Done

#### Task 5: VendorContractDocument repository + MinIO storage
- **File:** `src/procurement_bc/vendor/infrastructure/repository.py` (or separate file)
- **What:** Implement `VendorContractDocumentRepositoryInterface`. MinIO upload using existing `StorageService` pattern from report_bc. Bucket: `vendor-contracts`. Key pattern: `{company_id}/{vendor_id}/{contract_id}/{doc_id}/{filename}`.
- **Deps:** Tasks 1-3
- **Acceptance:** Upload stores file in MinIO, download retrieves, soft_delete marks is_deleted
- [x] Done

### Phase 3: Application

#### Task 6: CreateContractCommand + handler
- **File:** `src/procurement_bc/vendor/application/commands/create_contract.py`
- **What:** `CreateContractCommand(vendor_id, company_id, contract_type, title, start_date, end_date?, renewal_date?, auto_renewal?, annual_value?, currency?, security_clauses?, notes?, created_by)`. Handler validates vendor exists, creates VendorContract with status=draft, saves.
- **Deps:** Task 4
- **Acceptance:** Creates contract in draft status
- [x] Done

#### Task 7: UpdateContractCommand + handler
- **File:** `src/procurement_bc/vendor/application/commands/update_contract.py`
- **What:** `UpdateContractCommand(contract_id, vendor_id, company_id, ...)`. Handler finds contract, updates allowed fields (title, dates, value, clauses, notes), saves.
- **Deps:** Task 4
- **Acceptance:** Updates fields, rejects if not found or deleted
- [x] Done

#### Task 8: ChangeContractStatusCommand + handler
- **File:** `src/procurement_bc/vendor/application/commands/change_contract_status.py`
- **What:** `ChangeContractStatusCommand(contract_id, vendor_id, company_id, new_status)`. Handler finds contract, calls `change_status()` (validates transitions), saves.
- **Deps:** Task 4
- **Acceptance:** Valid transitions succeed, invalid raise `InvalidContractTransitionError`
- [x] Done

#### Task 9: SoftDeleteContractCommand + handler
- **File:** `src/procurement_bc/vendor/application/commands/soft_delete_contract.py`
- **What:** `SoftDeleteContractCommand(contract_id, vendor_id, company_id)`. Handler finds contract, marks is_deleted=true, saves.
- **Deps:** Task 4
- **Acceptance:** Contract marked deleted, no longer returned in queries
- [x] Done

#### Task 10: ListContractsQuery + handler
- **File:** `src/procurement_bc/vendor/application/queries/list_contracts.py`
- **What:** `ListContractsQuery(vendor_id, company_id, page, page_size, status?)`. Returns `tuple[list[ContractDto], int]`.
- **Deps:** Task 4
- **Acceptance:** Returns paginated list, filters by status, excludes soft-deleted
- [x] Done

#### Task 11: GetContractQuery + handler
- **File:** `src/procurement_bc/vendor/application/queries/get_contract.py`
- **What:** `GetContractQuery(contract_id, vendor_id, company_id)`. Returns `ContractDto` with document count.
- **Deps:** Task 4
- **Acceptance:** Returns contract detail or raises not found
- [x] Done

#### Task 12: UploadContractDocumentCommand + handler
- **File:** `src/procurement_bc/vendor/application/commands/upload_contract_document.py`
- **What:** `UploadContractDocumentCommand(contract_id, vendor_id, company_id, filename, content_type, size_bytes, file_data, uploaded_by)`. Handler validates contract exists, uploads to MinIO, creates document entity, saves.
- **Deps:** Tasks 4, 5
- **Acceptance:** File stored in MinIO, document record created
- [x] Done

#### Task 13: ListContractDocumentsQuery + handler
- **File:** `src/procurement_bc/vendor/application/queries/list_contract_documents.py`
- **What:** `ListContractDocumentsQuery(contract_id, vendor_id, company_id)`. Returns `list[DocumentDto]`.
- **Deps:** Task 5
- **Acceptance:** Returns non-deleted documents for contract
- [x] Done

#### Task 14: DownloadContractDocumentQuery + handler
- **File:** `src/procurement_bc/vendor/application/queries/download_contract_document.py`
- **What:** `DownloadContractDocumentQuery(document_id, contract_id, vendor_id, company_id)`. Returns file stream from MinIO + metadata.
- **Deps:** Task 5
- **Acceptance:** Returns file data and content type
- [x] Done

#### Task 15: SoftDeleteContractDocumentCommand + handler
- **File:** `src/procurement_bc/vendor/application/commands/soft_delete_contract_document.py`
- **What:** `SoftDeleteContractDocumentCommand(document_id, contract_id, vendor_id, company_id)`. Marks document as deleted.
- **Deps:** Task 5
- **Acceptance:** Document no longer returned in list queries
- [x] Done

#### Task 16: UpdateVendorCommand extension
- **File:** `src/procurement_bc/vendor/application/commands/update_vendor.py` (extend existing)
- **What:** Extend existing `UpdateVendorCommand` to accept `category`, `website`, `is_critical_ict` fields. Handler updates these on vendor entity.
- **Deps:** Task 1
- **Acceptance:** Existing update still works, new fields accepted and persisted
- [x] Done

#### Task 17: Contract auto-expiry Celery task
- **Files:** `core/tasks/vendor_contracts.py` (new), `core/celery.py` (extend beat_schedule)
- **What:** Daily Celery task: query active contracts with end_date < today, transition each to `expired` status. Idempotent — skip already expired. Add to beat_schedule (daily at 01:00 UTC).
- **Deps:** Task 4
- **Acceptance:** Active contracts past end_date auto-expire, no duplicates
- [x] Done

### Phase 4: HTTP

#### Task 18: Contract schemas
- **File:** `adapters/http/api/vendors/contract_schemas.py` (new)
- **What:** `CreateContractRequest`, `UpdateContractRequest`, `ChangeContractStatusRequest`, `ContractResponse`, `ContractListResponse`. Validation: title min 1 max 200, start_date required, contract_type enum, status enum.
- **Deps:** Tasks 6-11
- **Acceptance:** All schemas defined with proper validation
- [x] Done

#### Task 19: Contract document schemas
- **File:** `adapters/http/api/vendors/contract_document_schemas.py` (new)
- **What:** `DocumentResponse`, `DocumentListResponse`. Upload is multipart form, no request schema needed.
- **Deps:** Tasks 12-15
- **Acceptance:** Schemas defined
- [x] Done

#### Task 20: Contract router + dependencies
- **File:** `adapters/http/api/vendors/contract_router.py` (new), `adapters/http/api/vendors/contract_dependencies.py` (new)
- **What:** All contract endpoints: POST, GET list, GET detail, PUT, DELETE, POST change-status. Dependencies: `get_contract_repo()`. Auth: create/update/delete/status = admin, list/get = technician+.
- **Deps:** Tasks 18
- **Acceptance:** All endpoints working with proper auth and error handling
- [x] Done

#### Task 21: Contract document router
- **File:** `adapters/http/api/vendors/contract_document_router.py` (new)
- **What:** POST upload (multipart), GET list, GET download, DELETE. Auth: upload/delete = admin, list/download = technician+.
- **Deps:** Task 19
- **Acceptance:** Upload/download/delete working
- [x] Done

#### Task 22: Register routers in app.py
- **File:** `app.py`
- **What:** Import and include contract_router and contract_document_router under vendors prefix.
- **Deps:** Tasks 20-21
- **Acceptance:** Routers registered, endpoints accessible
- [x] Done

### Phase 5: Tests

#### Task 23: Unit tests — domain entities
- **File:** `tests/unit/procurement_bc/vendor/domain/test_contract_entities.py` (new)
- **What:** Test VendorContract.create validation, change_status valid/invalid transitions (all 6 valid + invalid combos), update, soft_delete. Test VendorContractDocument.create, soft_delete. Test Vendor extended fields.
- **Acceptance:** All domain logic covered
- [x] Done

#### Task 24: Unit tests — contract command handlers
- **File:** `tests/unit/procurement_bc/vendor/application/commands/test_contract_commands.py` (new)
- **What:** Test CreateContractCommandHandler, UpdateContractCommandHandler, ChangeContractStatusCommandHandler, SoftDeleteContractCommandHandler. Mock repos.
- **Acceptance:** All contract command handlers tested
- [x] Done

#### Task 25: Unit tests — contract document handlers
- **File:** `tests/unit/procurement_bc/vendor/application/commands/test_contract_document_commands.py` (new)
- **What:** Test UploadContractDocumentCommandHandler, SoftDeleteContractDocumentCommandHandler, ListContractDocumentsQueryHandler, DownloadContractDocumentQueryHandler. Mock repos + storage.
- **Acceptance:** All document handlers tested
- [x] Done

#### Task 26: Unit tests — contract query handlers
- **File:** `tests/unit/procurement_bc/vendor/application/queries/test_contract_queries.py` (new)
- **What:** Test ListContractsQueryHandler (pagination, status filter), GetContractQueryHandler (found, not found). Mock repo.
- **Acceptance:** All query handlers tested
- [x] Done

#### Task 27: Integration tests — contract endpoints
- **File:** `tests/integration/test_vendor_contracts_endpoints.py` (new)
- **What:** Test all contract endpoints: create (201), list (200, pagination, status filter), get (200), update (200), change status (200, invalid=422), soft delete (204). Auth: employee=403, technician list=200, admin all=200. Not found=404. Tenant isolation.
- **Acceptance:** All endpoints tested with real DB
- [x] Done

#### Task 28: Integration tests — contract document endpoints
- **File:** `tests/integration/test_vendor_contract_documents_endpoints.py` (new)
- **What:** Test upload (201), list (200), download (200 + correct content), soft delete (204). Auth checks. File not found after delete.
- **Acceptance:** All document endpoints tested
- [x] Done

### Phase 6: Frontend

#### Task 29: TypeScript types
- **File:** `web/app/src/types/index.ts`
- **What:** Add `VendorContract`, `VendorContractDocument` interfaces. Extend `Vendor` with `is_critical_ict`, `risk_level`, `website`, `category`.
- **Acceptance:** All types defined
- [x] Done

#### Task 30: Update VendorListPage
- **File:** `web/app/src/pages/admin/VendorListPage.tsx`
- **What:** Add category badge column. Add risk_level badge column (color-coded: low=green, medium=yellow, high=orange, critical=red). Make vendor name a link to `/vendors/:id` detail page. Update create/edit modal to include category, website, is_critical_ict fields.
- **Acceptance:** List shows new columns, links to detail, modal has new fields
- [x] Done

#### Task 31: i18n EN/ES translations
- **Files:** `web/app/src/locales/en.ts`, `web/app/src/locales/es.ts`
- **What:** All contract-related keys: page titles, form fields, status names, contract types, security clause labels, document labels, buttons, table headers.
- **Acceptance:** All strings translated EN + ES
- [x] Done
