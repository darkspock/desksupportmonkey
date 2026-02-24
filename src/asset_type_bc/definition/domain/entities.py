import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

import ulid


class _UnsetType:
    """Sentinel to distinguish 'not provided' from None."""
    pass


_UNSET = _UnsetType()


@dataclass
class AssetTypeDefinition:
    id: str
    company_id: str
    code: str
    name: str
    icon: Optional[str]
    is_active: bool
    sort_order: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def create(
        cls,
        company_id: str,
        name: str,
        icon: Optional[str] = None,
        sort_order: int = 0,
    ) -> "AssetTypeDefinition":
        code = cls._slugify(name)
        return cls(
            id=str(ulid.new()),
            company_id=company_id,
            code=code,
            name=name.strip(),
            icon=icon.strip() if icon else None,
            is_active=True,
            sort_order=sort_order,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

    @staticmethod
    def _slugify(name: str) -> str:
        slug = name.strip().lower()
        slug = re.sub(r"[^a-z0-9\s_]", "", slug)
        slug = re.sub(r"\s+", "_", slug)
        slug = re.sub(r"_+", "_", slug)
        slug = slug.strip("_")
        return slug[:50]

    def update(
        self,
        name: Optional[str] = None,
        icon: Optional[str] | _UnsetType = _UNSET,
        is_active: Optional[bool] = None,
    ) -> None:
        if name is not None:
            self.name = name.strip()
            self.code = self._slugify(name)
        if not isinstance(icon, _UnsetType):
            self.icon = icon.strip() if icon else None
        if is_active is not None:
            self.is_active = is_active
        self.updated_at = datetime.now(timezone.utc)
