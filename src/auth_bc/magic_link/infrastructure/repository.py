import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import delete, func, select, update
from sqlalchemy.orm import Session

from src.auth_bc.magic_link.domain.entities import MagicLink
from src.auth_bc.magic_link.domain.repository import MagicLinkRepositoryInterface
from src.auth_bc.magic_link.infrastructure.models import MagicLinkModel

logger = logging.getLogger(__name__)


class MagicLinkRepository(MagicLinkRepositoryInterface):
    def __init__(self, session: Session):
        self.session = session

    def save(self, magic_link: MagicLink) -> MagicLink:
        model = MagicLinkModel(
            id=magic_link.id,
            email=magic_link.email,
            token=magic_link.token,
            expires_at=magic_link.expires_at,
            used_at=magic_link.used_at,
            company_id=magic_link.company_id,
            created_at=magic_link.created_at,
        )
        self.session.add(model)
        self.session.flush()
        return magic_link

    def find_by_token(self, token: str) -> Optional[MagicLink]:
        model = self.session.execute(
            select(MagicLinkModel).where(MagicLinkModel.token == token)
        ).scalar_one_or_none()
        return self._to_entity(model) if model else None

    def update_used_at(self, magic_link_id: str, used_at: datetime) -> None:
        self.session.execute(
            update(MagicLinkModel)
            .where(MagicLinkModel.id == magic_link_id)
            .values(used_at=used_at)
        )
        self.session.flush()

    def count_recent_by_email(self, email: str, since: datetime) -> int:
        return (
            self.session.execute(
                select(func.count()).select_from(MagicLinkModel)
                .where(
                    MagicLinkModel.email == email.lower().strip(),
                    MagicLinkModel.created_at >= since,
                )
            ).scalar()
        ) or 0

    def delete_older_than(self, days: int) -> int:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        result = self.session.execute(
            delete(MagicLinkModel)
            .where(MagicLinkModel.created_at < cutoff)
        )
        self.session.flush()
        count = result.rowcount
        logger.info("Deleted %d expired magic links older than %d days", count, days)
        return count

    @staticmethod
    def _to_entity(model: MagicLinkModel) -> MagicLink:
        return MagicLink(
            id=model.id,
            email=model.email,
            token=model.token,
            expires_at=model.expires_at,
            used_at=model.used_at,
            created_at=model.created_at,
            company_id=model.company_id,
        )
