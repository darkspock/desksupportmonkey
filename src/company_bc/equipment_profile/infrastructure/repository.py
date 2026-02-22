from typing import Optional

import ulid
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.asset_bc.asset.domain.enums import AssetType
from src.company_bc.equipment_profile.domain.entities import (
    EquipmentProfile,
    EquipmentProfileItem,
)
from src.company_bc.equipment_profile.domain.repository import (
    EquipmentProfileRepositoryInterface,
)
from src.company_bc.equipment_profile.infrastructure.models import (
    EquipmentProfileItemModel,
    EquipmentProfileModel,
)


class EquipmentProfileRepository(
    EquipmentProfileRepositoryInterface,
):
    def __init__(self, session: Session):
        self.session = session

    def save(
        self, profile: EquipmentProfile,
    ) -> EquipmentProfile:
        existing = self.session.execute(
            select(EquipmentProfileModel).where(
                EquipmentProfileModel.id == profile.id,
            )
        ).unique().scalar_one_or_none()

        if existing:
            existing.is_active = profile.is_active
            existing.items.clear()
            self.session.flush()
            for item in profile.items:
                existing.items.append(
                    EquipmentProfileItemModel(
                        id=item.id or str(ulid.new()),
                        profile_id=profile.id,
                        asset_type=item.asset_type.value,
                        quantity=item.quantity,
                        preferred_brand=item.preferred_brand,
                        preferred_model=item.preferred_model,
                        min_ram_gb=item.min_ram_gb,
                        min_storage_gb=item.min_storage_gb,
                        budget_cents=item.budget_cents,
                    )
                )
        else:
            model = EquipmentProfileModel(
                id=profile.id,
                company_id=profile.company_id,
                department_id=profile.department_id,
                employee_role_id=profile.employee_role_id,
                is_active=profile.is_active,
                items=[
                    EquipmentProfileItemModel(
                        id=i.id or str(ulid.new()),
                        profile_id=profile.id,
                        asset_type=i.asset_type.value,
                        quantity=i.quantity,
                        preferred_brand=i.preferred_brand,
                        preferred_model=i.preferred_model,
                        min_ram_gb=i.min_ram_gb,
                        min_storage_gb=i.min_storage_gb,
                        budget_cents=i.budget_cents,
                    )
                    for i in profile.items
                ],
            )
            self.session.add(model)

        self.session.flush()
        return profile

    def find_by_id(
        self, profile_id: str, company_id: str,
    ) -> Optional[EquipmentProfile]:
        model = self.session.execute(
            select(EquipmentProfileModel).where(
                EquipmentProfileModel.id == profile_id,
                EquipmentProfileModel.company_id
                == company_id,
            )
        ).unique().scalar_one_or_none()
        return self._to_entity(model) if model else None

    def find_active(
        self,
        company_id: str,
        department_id: str,
        employee_role_id: Optional[str],
    ) -> Optional[EquipmentProfile]:
        model = self.session.execute(
            select(EquipmentProfileModel).where(
                EquipmentProfileModel.company_id
                == company_id,
                EquipmentProfileModel.department_id
                == department_id,
                EquipmentProfileModel.employee_role_id == employee_role_id,
                EquipmentProfileModel.is_active.is_(True),
            )
        ).unique().scalar_one_or_none()
        return self._to_entity(model) if model else None

    def find_all(
        self,
        company_id: str,
        page: int,
        page_size: int,
        department_id: Optional[str] = None,
        employee_role_id: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> tuple[list[EquipmentProfile], int]:
        stmt = select(EquipmentProfileModel).where(
            EquipmentProfileModel.company_id == company_id,
        )
        if department_id:
            stmt = stmt.where(
                EquipmentProfileModel.department_id
                == department_id,
            )
        if employee_role_id:
            stmt = stmt.where(
                EquipmentProfileModel.employee_role_id == employee_role_id,
            )
        if is_active is not None:
            stmt = stmt.where(
                EquipmentProfileModel.is_active == is_active,
            )
        total = self.session.execute(
            select(func.count()).select_from(
                stmt.subquery(),
            )
        ).scalar()
        models = (
            self.session.execute(
                stmt.order_by(
                    EquipmentProfileModel.created_at.desc(),
                )
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
            .scalars()
            .unique()
            .all()
        )
        return (
            [self._to_entity(m) for m in models],
            total or 0,
        )

    def delete(self, profile_id: str) -> None:
        model = self.session.execute(
            select(EquipmentProfileModel).where(
                EquipmentProfileModel.id == profile_id,
            )
        ).unique().scalar_one_or_none()
        if model:
            self.session.delete(model)
            self.session.flush()

    @staticmethod
    def _to_entity(
        model: EquipmentProfileModel,
    ) -> EquipmentProfile:
        return EquipmentProfile(
            id=model.id,
            company_id=model.company_id,
            department_id=model.department_id,
            employee_role_id=model.employee_role_id,
            is_active=model.is_active,
            items=[
                EquipmentProfileItem(
                    id=i.id,
                    profile_id=i.profile_id,
                    asset_type=AssetType(i.asset_type),
                    quantity=i.quantity,
                    preferred_brand=i.preferred_brand,
                    preferred_model=i.preferred_model,
                    min_ram_gb=i.min_ram_gb,
                    min_storage_gb=i.min_storage_gb,
                    budget_cents=i.budget_cents,
                )
                for i in model.items
            ],
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
