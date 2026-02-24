from fastapi import Depends
from sqlalchemy.orm import Session

from core.database import get_db
from src.custom_field_bc.definition.application.services.enrichment_service import (
    CustomFieldEnrichmentService,
)
from src.custom_field_bc.definition.application.services.validation_service import (
    CustomFieldValidationService,
)
from src.custom_field_bc.definition.infrastructure.repository import (
    CustomFieldDefinitionRepository,
)


def get_cf_definition_repo(
    db: Session = Depends(get_db),
) -> CustomFieldDefinitionRepository:
    return CustomFieldDefinitionRepository(db)


def get_cf_validation_service(
    db: Session = Depends(get_db),
) -> CustomFieldValidationService:
    return CustomFieldValidationService(CustomFieldDefinitionRepository(db))


def get_cf_enrichment_service(
    db: Session = Depends(get_db),
) -> CustomFieldEnrichmentService:
    return CustomFieldEnrichmentService(CustomFieldDefinitionRepository(db))
