from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import ulid

from src.company_bc.assignment_config.domain.enums import (
    AIProvider,
)


@dataclass
class CompanyAssignmentAIConfig:
    id: str
    company_id: str
    provider: AIProvider
    prompt_template: str
    model: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def create(
        cls,
        company_id: str,
        provider: AIProvider,
        prompt_template: str,
        model: Optional[str] = None,
        id: Optional[str] = None,
    ) -> "CompanyAssignmentAIConfig":
        return cls(
            id=id or str(ulid.new()),
            company_id=company_id,
            provider=provider,
            prompt_template=prompt_template,
            model=model,
        )
