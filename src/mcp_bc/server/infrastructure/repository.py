from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from src.mcp_bc.server.domain.entities import ApiKey
from src.mcp_bc.server.domain.repository import ApiKeyRepositoryInterface
from src.mcp_bc.server.infrastructure.models import ApiKeyModel


class ApiKeyRepository(ApiKeyRepositoryInterface):
    def __init__(self, session: Session):
        self.session = session

    def save(self, api_key: ApiKey) -> ApiKey:
        existing = self.session.execute(
            select(ApiKeyModel).where(ApiKeyModel.id == api_key.id)
        ).scalar_one_or_none()

        if existing:
            existing.name = api_key.name
            existing.is_active = api_key.is_active
            existing.last_used_at = api_key.last_used_at
            model = existing
        else:
            model = ApiKeyModel(
                id=api_key.id,
                user_id=api_key.user_id,
                key_hash=api_key.key_hash,
                name=api_key.name,
                is_active=api_key.is_active,
            )
            self.session.add(model)

        self.session.flush()
        self.session.refresh(model)
        return self._to_entity(model)

    def find_by_id(self, key_id: str, user_id: str) -> Optional[ApiKey]:
        model = self.session.execute(
            select(ApiKeyModel).where(
                ApiKeyModel.id == key_id,
                ApiKeyModel.user_id == user_id,
            )
        ).scalar_one_or_none()
        return self._to_entity(model) if model else None

    def find_all_by_user(self, user_id: str) -> list[ApiKey]:
        models = self.session.execute(
            select(ApiKeyModel)
            .where(ApiKeyModel.user_id == user_id)
            .order_by(ApiKeyModel.created_at.desc())
        ).scalars().all()
        return [self._to_entity(m) for m in models]

    def count_active_by_user(self, user_id: str) -> int:
        result = self.session.execute(
            select(func.count()).select_from(ApiKeyModel).where(
                ApiKeyModel.user_id == user_id,
                ApiKeyModel.is_active.is_(True),
            )
        ).scalar()
        return result or 0

    def find_all_active(self) -> list[ApiKey]:
        models = self.session.execute(
            select(ApiKeyModel).where(ApiKeyModel.is_active.is_(True))
        ).scalars().all()
        return [self._to_entity(m) for m in models]

    def find_active_by_hash(self, key_hash: str) -> Optional[ApiKey]:
        model = self.session.execute(
            select(ApiKeyModel).where(
                ApiKeyModel.key_hash == key_hash,
                ApiKeyModel.is_active.is_(True),
            )
        ).scalar_one_or_none()
        return self._to_entity(model) if model else None

    def update_last_used(self, key_id: str) -> None:
        self.session.execute(
            update(ApiKeyModel)
            .where(ApiKeyModel.id == key_id)
            .values(last_used_at=datetime.now(timezone.utc))
        )

    @staticmethod
    def _to_entity(model: ApiKeyModel) -> ApiKey:
        return ApiKey(
            id=model.id,
            user_id=model.user_id,
            key_hash=model.key_hash,
            name=model.name,
            created_at=model.created_at,
            last_used_at=model.last_used_at,
            is_active=model.is_active,
        )
