from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.procurement_bc.vendor.domain.entities import (
    Vendor,
)
from src.procurement_bc.vendor.domain.repository import (
    VendorRepositoryInterface,
)
from src.procurement_bc.vendor.infrastructure.models import (
    VendorModel,
)


class VendorRepository(VendorRepositoryInterface):
    def __init__(self, session: Session):
        self.session = session

    def save(self, vendor: Vendor) -> Vendor:
        existing = self.session.execute(
            select(VendorModel).where(
                VendorModel.id == vendor.id,
            )
        ).scalar_one_or_none()

        if existing:
            existing.name = vendor.name
            existing.contact_email = vendor.contact_email
            existing.phone = vendor.phone
            existing.address = vendor.address
            existing.notes = vendor.notes
            existing.is_active = vendor.is_active
        else:
            model = VendorModel(
                id=vendor.id,
                company_id=vendor.company_id,
                name=vendor.name,
                contact_email=vendor.contact_email,
                phone=vendor.phone,
                address=vendor.address,
                notes=vendor.notes,
                is_active=vendor.is_active,
            )
            self.session.add(model)

        self.session.flush()
        return vendor

    def find_by_id(
        self, vendor_id: str, company_id: str,
    ) -> Optional[Vendor]:
        model = self.session.execute(
            select(VendorModel).where(
                VendorModel.id == vendor_id,
                VendorModel.company_id == company_id,
            )
        ).scalar_one_or_none()
        return self._to_entity(model) if model else None

    def find_all(
        self,
        company_id: str,
        page: int,
        page_size: int,
        search: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> tuple[list[Vendor], int]:
        stmt = select(VendorModel).where(
            VendorModel.company_id == company_id,
        )
        if search:
            stmt = stmt.where(
                VendorModel.name.ilike(f"%{search}%"),
            )
        if is_active is not None:
            stmt = stmt.where(
                VendorModel.is_active == is_active,
            )

        total = self.session.execute(
            select(func.count()).select_from(
                stmt.subquery(),
            )
        ).scalar()

        models = (
            self.session.execute(
                stmt.order_by(VendorModel.name)
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
            .scalars()
            .all()
        )
        return (
            [self._to_entity(m) for m in models],
            total or 0,
        )

    def find_by_name(
        self, name: str, company_id: str,
    ) -> Optional[Vendor]:
        model = self.session.execute(
            select(VendorModel).where(
                VendorModel.name == name,
                VendorModel.company_id == company_id,
            )
        ).scalar_one_or_none()
        return self._to_entity(model) if model else None

    @staticmethod
    def _to_entity(model: VendorModel) -> Vendor:
        return Vendor(
            id=model.id,
            company_id=model.company_id,
            name=model.name,
            is_active=model.is_active,
            contact_email=model.contact_email,
            phone=model.phone,
            address=model.address,
            notes=model.notes,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
