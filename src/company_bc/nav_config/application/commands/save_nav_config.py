import logging
from dataclasses import dataclass, field
from typing import Dict, List

from src.company_bc.nav_config.domain.entities import CompanyNavConfig
from src.company_bc.nav_config.domain.repository import (
    NavConfigRepositoryInterface,
)
from src.framework.application.command_bus import (
    Command,
    CommandHandler,
)

logger = logging.getLogger(__name__)

CONFIGURABLE_ROLES = {"admin", "employee", "technician", "procurement_manager"}


class InvalidRoleError(Exception):
    pass


@dataclass
class SaveNavConfigCommand(Command):
    company_id: str
    hidden_nav_items: Dict[str, List[str]] = field(default_factory=dict)
    performed_by: str = ""


class SaveNavConfigCommandHandler(
    CommandHandler[SaveNavConfigCommand],
):
    def __init__(
        self,
        nav_config_repo: NavConfigRepositoryInterface,
    ):
        self.nav_config_repo = nav_config_repo

    def handle(self, command: SaveNavConfigCommand) -> None:
        # Validate that only configurable roles are included
        for role_key in command.hidden_nav_items:
            if role_key not in CONFIGURABLE_ROLES:
                raise InvalidRoleError(
                    f"Cannot configure nav items for role: {role_key}",
                )

        # Strip empty lists to keep data clean
        cleaned: Dict[str, List[str]] = {
            k: v
            for k, v in command.hidden_nav_items.items()
            if v
        }

        existing = self.nav_config_repo.find_by_company(
            command.company_id,
        )
        if existing:
            existing.hidden_nav_items = cleaned
            self.nav_config_repo.save(existing)
        else:
            config = CompanyNavConfig.create(
                company_id=command.company_id,
                hidden_nav_items=cleaned,
            )
            self.nav_config_repo.save(config)

        logger.info(
            "Nav config saved for company %s",
            command.company_id,
        )
