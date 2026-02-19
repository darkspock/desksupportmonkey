import logging
from dataclasses import dataclass
from typing import Optional

from src.company_bc.assignment_config.domain.enums import AIProvider
from src.company_bc.classification_config.domain.entities import (
    CompanyClassificationConfig,
)
from src.company_bc.classification_config.domain.repository import (
    ClassificationConfigRepositoryInterface,
)
from src.framework.application.command_bus import Command, CommandHandler

logger = logging.getLogger(__name__)


class InvalidProviderError(Exception):
    pass


class InvalidThresholdError(Exception):
    pass


class InvalidTimeoutError(Exception):
    pass


@dataclass
class SaveClassificationConfigCommand(Command):
    company_id: str
    is_enabled: bool
    provider: str
    confidence_threshold: float
    timeout_seconds: int
    model: Optional[str] = None
    prompt_template: Optional[str] = None
    performed_by: str = ""


class SaveClassificationConfigCommandHandler(
    CommandHandler[SaveClassificationConfigCommand],
):
    def __init__(
        self,
        config_repo: ClassificationConfigRepositoryInterface,
    ):
        self.config_repo = config_repo

    def handle(
        self, command: SaveClassificationConfigCommand,
    ) -> None:
        try:
            provider = AIProvider(command.provider)
        except ValueError:
            raise InvalidProviderError(
                f"Invalid provider: {command.provider}",
            )

        if not (0.5 <= command.confidence_threshold <= 1.0):
            raise InvalidThresholdError(
                f"Threshold must be between 0.5 and 1.0, got {command.confidence_threshold}",
            )

        if command.timeout_seconds < 1:
            raise InvalidTimeoutError(
                f"Timeout must be >= 1, got {command.timeout_seconds}",
            )

        existing = self.config_repo.find_by_company(command.company_id)
        if existing:
            existing.is_enabled = command.is_enabled
            existing.provider = provider
            existing.model = command.model
            existing.confidence_threshold = command.confidence_threshold
            existing.prompt_template = command.prompt_template
            existing.timeout_seconds = command.timeout_seconds
            self.config_repo.save(existing)
        else:
            config = CompanyClassificationConfig.create(
                company_id=command.company_id,
                is_enabled=command.is_enabled,
                provider=provider,
                model=command.model,
                confidence_threshold=command.confidence_threshold,
                prompt_template=command.prompt_template,
                timeout_seconds=command.timeout_seconds,
            )
            self.config_repo.save(config)

        logger.info(
            "Classification config saved for company %s",
            command.company_id,
        )
