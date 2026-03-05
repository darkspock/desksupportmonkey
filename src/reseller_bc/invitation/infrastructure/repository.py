from datetime import datetime
from typing import Optional

from sqlalchemy import and_, func, select, text
from sqlalchemy.orm import Session

from src.reseller_bc.invitation.domain.entities import ResellerInvitation
from src.reseller_bc.invitation.domain.enums import InvitationStatus
from src.reseller_bc.invitation.domain.repository import ResellerInvitationRepositoryInterface
from src.reseller_bc.invitation.infrastructure.models import ResellerInvitationModel


class ResellerInvitationRepository(ResellerInvitationRepositoryInterface):
    def __init__(self, session: Session):
        self.session = session

    def save(self, invitation: ResellerInvitation) -> None:
        existing = self.session.execute(
            select(ResellerInvitationModel).where(ResellerInvitationModel.id == invitation.id)
        ).scalar_one_or_none()
        if existing:
            existing.reseller_id = invitation.reseller_id
            existing.email = invitation.email
            existing.status = invitation.status.value
            existing.expires_at = invitation.expires_at
        else:
            model = ResellerInvitationModel(
                id=invitation.id,
                reseller_id=invitation.reseller_id,
                email=invitation.email,
                status=invitation.status.value,
                expires_at=invitation.expires_at,
            )
            self.session.add(model)
        self.session.flush()

    def find_pending_by_email(self, email: str) -> Optional[ResellerInvitation]:
        now = datetime.utcnow()
        model = self.session.execute(
            select(ResellerInvitationModel)
            .where(and_(
                ResellerInvitationModel.email == email.lower().strip(),
                ResellerInvitationModel.status == InvitationStatus.PENDING.value,
                ResellerInvitationModel.expires_at > now,
            ))
            .order_by(ResellerInvitationModel.created_at.asc())
            .limit(1)
        ).scalar_one_or_none()
        return self._to_entity(model) if model else None

    def count_pending_by_reseller_id(self, reseller_id: str) -> int:
        return (
            self.session.execute(
                select(func.count()).select_from(ResellerInvitationModel)
                .where(and_(
                    ResellerInvitationModel.reseller_id == reseller_id,
                    ResellerInvitationModel.status == InvitationStatus.PENDING.value,
                ))
            ).scalar()
        ) or 0

    def find_by_reseller_id(self, reseller_id: str, offset: int = 0, limit: int = 50) -> list[ResellerInvitation]:
        models = self.session.execute(
            select(ResellerInvitationModel)
            .where(ResellerInvitationModel.reseller_id == reseller_id)
            .order_by(ResellerInvitationModel.created_at.desc())
            .offset(offset)
            .limit(limit)
        ).scalars().all()
        return [self._to_entity(m) for m in models]

    def count_by_reseller_id(self, reseller_id: str) -> int:
        return (
            self.session.execute(
                select(func.count()).select_from(ResellerInvitationModel)
                .where(ResellerInvitationModel.reseller_id == reseller_id)
            ).scalar()
        ) or 0

    def find_expired_pending(self) -> list[ResellerInvitation]:
        now = datetime.utcnow()
        models = self.session.execute(
            select(ResellerInvitationModel)
            .where(and_(
                ResellerInvitationModel.status == InvitationStatus.PENDING.value,
                ResellerInvitationModel.expires_at <= now,
            ))
        ).scalars().all()
        return [self._to_entity(m) for m in models]

    def cancel_by_id(self, invitation_id: str, reseller_id: str) -> Optional[ResellerInvitation]:
        model = self.session.execute(
            select(ResellerInvitationModel)
            .where(and_(
                ResellerInvitationModel.id == invitation_id,
                ResellerInvitationModel.reseller_id == reseller_id,
                ResellerInvitationModel.status == InvitationStatus.PENDING.value,
            ))
        ).scalar_one_or_none()
        if model is None:
            return None
        model.status = InvitationStatus.CANCELLED.value
        self.session.flush()
        return self._to_entity(model)

    @staticmethod
    def _to_entity(model: ResellerInvitationModel) -> ResellerInvitation:
        return ResellerInvitation(
            id=model.id,
            reseller_id=model.reseller_id,
            email=model.email,
            status=InvitationStatus(model.status),
            expires_at=model.expires_at,
            created_at=model.created_at,
        )
