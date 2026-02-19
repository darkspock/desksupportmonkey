from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.shipping_bc.address.domain.entities import (
    ShippingAddress,
)
from src.shipping_bc.address.domain.repository import (
    ShippingAddressRepositoryInterface,
)
from src.shipping_bc.address.infrastructure.models import (
    ShippingAddressModel,
)


class ShippingAddressRepository(
    ShippingAddressRepositoryInterface,
):

    def __init__(self, session: Session):
        self.session = session

    def save(
        self, address: ShippingAddress,
    ) -> ShippingAddress:
        existing = (
            self.session.execute(
                select(ShippingAddressModel).where(
                    ShippingAddressModel.id == address.id,
                )
            )
            .scalar_one_or_none()
        )

        if existing:
            existing.label = address.label
            existing.recipient_name = (
                address.recipient_name
            )
            existing.street_line_1 = address.street_line_1
            existing.street_line_2 = address.street_line_2
            existing.city = address.city
            existing.state = address.state
            existing.postal_code = address.postal_code
            existing.country = address.country
            existing.phone = address.phone
            existing.user_id = address.user_id
            existing.is_office = address.is_office
            existing.is_active = address.is_active
        else:
            model = ShippingAddressModel(
                id=address.id,
                company_id=address.company_id,
                label=address.label,
                recipient_name=address.recipient_name,
                street_line_1=address.street_line_1,
                street_line_2=address.street_line_2,
                city=address.city,
                state=address.state,
                postal_code=address.postal_code,
                country=address.country,
                phone=address.phone,
                user_id=address.user_id,
                is_office=address.is_office,
                is_active=address.is_active,
            )
            self.session.add(model)

        self.session.flush()
        return address

    def find_by_id(
        self, address_id: str, company_id: str,
    ) -> Optional[ShippingAddress]:
        model = (
            self.session.execute(
                select(ShippingAddressModel).where(
                    ShippingAddressModel.id == address_id,
                    ShippingAddressModel.company_id
                    == company_id,
                )
            )
            .scalar_one_or_none()
        )
        if not model:
            return None
        return self._to_entity(model)

    def find_all(
        self,
        company_id: str,
        page: int,
        page_size: int,
        user_id: Optional[str] = None,
        is_office: Optional[bool] = None,
        is_active: Optional[bool] = None,
    ) -> tuple[list[ShippingAddress], int]:
        stmt = select(ShippingAddressModel).where(
            ShippingAddressModel.company_id == company_id,
        )
        if user_id:
            stmt = stmt.where(
                ShippingAddressModel.user_id == user_id,
            )
        if is_office is not None:
            stmt = stmt.where(
                ShippingAddressModel.is_office
                == is_office,
            )
        if is_active is not None:
            stmt = stmt.where(
                ShippingAddressModel.is_active
                == is_active,
            )

        total = self.session.execute(
            select(func.count()).select_from(
                stmt.subquery(),
            )
        ).scalar()

        models = (
            self.session.execute(
                stmt.order_by(
                    ShippingAddressModel.label.asc(),
                )
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
            .scalars()
            .all()
        )

        return [self._to_entity(m) for m in models], (
            total or 0
        )

    def find_by_user_id(
        self, user_id: str, company_id: str,
    ) -> list[ShippingAddress]:
        models = (
            self.session.execute(
                select(ShippingAddressModel).where(
                    ShippingAddressModel.user_id
                    == user_id,
                    ShippingAddressModel.company_id
                    == company_id,
                    ShippingAddressModel.is_active
                    == True,  # noqa: E712
                )
            )
            .scalars()
            .all()
        )
        return [self._to_entity(m) for m in models]

    @staticmethod
    def _to_entity(
        model: ShippingAddressModel,
    ) -> ShippingAddress:
        return ShippingAddress(
            id=model.id,
            company_id=model.company_id,
            label=model.label,
            street_line_1=model.street_line_1,
            city=model.city,
            state=model.state,
            postal_code=model.postal_code,
            country=model.country,
            street_line_2=model.street_line_2,
            recipient_name=model.recipient_name,
            phone=model.phone,
            user_id=model.user_id,
            is_office=model.is_office,
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
