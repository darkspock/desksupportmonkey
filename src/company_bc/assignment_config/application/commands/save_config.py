import logging
from dataclasses import dataclass
from typing import Optional

from src.company_bc.assignment_config.domain.entities import (
    CompanyAssignmentAIConfig,
)
from src.company_bc.assignment_config.domain.enums import (
    AIProvider,
)
from src.company_bc.assignment_config.domain.repository import (
    AssignmentConfigRepositoryInterface,
)
from src.framework.application.command_bus import (
    Command,
    CommandHandler,
)

logger = logging.getLogger(__name__)


class InvalidProviderError(Exception):
    pass


@dataclass
class SaveCompanyAIConfigCommand(Command):
    company_id: str
    provider: str
    prompt_template: str
    model: Optional[str] = None
    performed_by: str = ""


class SaveCompanyAIConfigCommandHandler(
    CommandHandler[SaveCompanyAIConfigCommand],
):
    def __init__(
        self,
        config_repo: AssignmentConfigRepositoryInterface,
    ):
        self.config_repo = config_repo

    def handle(
        self, command: SaveCompanyAIConfigCommand,
    ) -> None:
        try:
            provider = AIProvider(command.provider)
        except ValueError:
            raise InvalidProviderError(
                f"Invalid provider: {command.provider}",
            )

        existing = self.config_repo.find_by_company(
            command.company_id,
        )
        if existing:
            existing.provider = provider
            existing.prompt_template = (
                command.prompt_template
            )
            existing.model = command.model
            self.config_repo.save(existing)
        else:
            config = CompanyAssignmentAIConfig.create(
                company_id=command.company_id,
                provider=provider,
                prompt_template=command.prompt_template,
                model=command.model,
            )
            self.config_repo.save(config)

        logger.info(
            "AI config saved for company %s",
            command.company_id,
        )
