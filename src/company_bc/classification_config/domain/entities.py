from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import ulid

from src.company_bc.assignment_config.domain.enums import AIProvider


@dataclass
class CompanyClassificationConfig:
    id: str
    company_id: str
    is_enabled: bool
    provider: AIProvider
    model: Optional[str]
    confidence_threshold: float
    prompt_template: Optional[str]
    timeout_seconds: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def create(
        cls,
        company_id: str,
        is_enabled: bool,
        provider: AIProvider,
        confidence_threshold: float,
        timeout_seconds: int,
        model: Optional[str] = None,
        prompt_template: Optional[str] = None,
        id: Optional[str] = None,
    ) -> "CompanyClassificationConfig":
        return cls(
            id=id or str(ulid.new()),
            company_id=company_id,
            is_enabled=is_enabled,
            provider=provider,
            model=model,
            confidence_threshold=confidence_threshold,
            prompt_template=prompt_template,
            timeout_seconds=timeout_seconds,
        )
