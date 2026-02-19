from fastapi import Depends
from sqlalchemy.orm import Session

from core.database import get_db
from src.asset_bc.asset.infrastructure.repository import (
    AssetRepository,
)
from src.auth_bc.user.infrastructure.repository import (
    UserRepository,
)
from src.company_bc.assignment_config.infrastructure.repository import (  # noqa: E501
    AssignmentConfigRepository,
)
from src.company_bc.classification_config.infrastructure.repository import (  # noqa: E501
    ClassificationConfigRepository,
)
from src.company_bc.equipment_profile.infrastructure.repository import (  # noqa: E501
    EquipmentProfileRepository,
)
from src.company_bc.department.infrastructure.repository import (
    DepartmentRepository,
)
from src.request_bc.request.infrastructure.repository import (
    RequestRepository,
)


def get_request_repo(
    db: Session = Depends(get_db),
) -> RequestRepository:
    return RequestRepository(db)


def get_user_repo(
    db: Session = Depends(get_db),
) -> UserRepository:
    return UserRepository(db)


def get_asset_repo(
    db: Session = Depends(get_db),
) -> AssetRepository:
    return AssetRepository(db)


def get_profile_repo(
    db: Session = Depends(get_db),
) -> EquipmentProfileRepository:
    return EquipmentProfileRepository(db)


def get_config_repo(
    db: Session = Depends(get_db),
) -> AssignmentConfigRepository:
    return AssignmentConfigRepository(db)


def get_department_repo(
    db: Session = Depends(get_db),
) -> DepartmentRepository:
    return DepartmentRepository(db)


def get_classification_config_repo(
    db: Session = Depends(get_db),
) -> ClassificationConfigRepository:
    return ClassificationConfigRepository(db)
