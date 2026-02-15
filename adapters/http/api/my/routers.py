import logging

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from adapters.http.api.auth.dependencies import get_current_user
from adapters.http.api.my.schemas import MyEquipmentResponse
from core.database import get_db
from src.auth_bc.user.domain.entities import User
from src.asset_bc.asset.application.queries.my_equipment import (
    MyEquipmentQuery,
    MyEquipmentQueryHandler,
)
from src.asset_bc.asset.domain.entities import Asset
from src.asset_bc.asset.infrastructure.repository import AssetRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/my", tags=["my"])


@router.get("/equipment")
def my_equipment(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    handler = MyEquipmentQueryHandler(asset_repo=AssetRepository(db))
    assets = handler.handle(
        MyEquipmentQuery(user_id=current_user.id, company_id=current_user.company_id)
    )
    return {
        "data": [
            MyEquipmentResponse(
                id=a.id,
                type=a.type.value,
                brand=a.brand,
                model=a.model,
                serial_number=a.serial_number,
                created_at=a.created_at,
            ).model_dump(mode="json")
            for a in assets
        ]
    }
