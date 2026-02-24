from fastapi import Depends
from sqlalchemy.orm import Session

from core.database import get_db
from src.asset_type_bc.definition.infrastructure.repository import (
    AssetTypeDefinitionRepository,
)


def get_asset_type_repo(
    db: Session = Depends(get_db),
) -> AssetTypeDefinitionRepository:
    return AssetTypeDefinitionRepository(db)
