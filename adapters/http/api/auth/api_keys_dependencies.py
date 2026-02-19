from fastapi import Depends
from sqlalchemy.orm import Session

from core.database import get_db
from src.mcp_bc.server.infrastructure.repository import ApiKeyRepository


def get_api_key_repo(db: Session = Depends(get_db)) -> ApiKeyRepository:
    return ApiKeyRepository(db)
