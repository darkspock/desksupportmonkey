import secrets
from dataclasses import dataclass
from typing import Optional

import bcrypt

from src.framework.application.command_bus import Command, CommandHandler
from src.mcp_bc.server.domain.entities import ApiKey
from src.mcp_bc.server.domain.repository import ApiKeyRepositoryInterface

MAX_ACTIVE_KEYS = 10
KEY_PREFIX = "dsm_"


class MaxApiKeysReachedError(Exception):
    pass


def generate_api_key() -> tuple[str, str]:
    """Generate a raw API key and its bcrypt hash.

    Returns:
        Tuple of (raw_key, key_hash).
        raw_key format: dsm_ + 40 hex chars (44 chars total).
    """
    raw_key = KEY_PREFIX + secrets.token_hex(20)
    key_hash = bcrypt.hashpw(raw_key.encode(), bcrypt.gensalt()).decode()
    return raw_key, key_hash


@dataclass
class CreateApiKeyCommand(Command):
    user_id: str
    name: str
    key_hash: str
    id: Optional[str] = None


class CreateApiKeyCommandHandler(CommandHandler[CreateApiKeyCommand]):
    def __init__(self, api_key_repo: ApiKeyRepositoryInterface):
        self.api_key_repo = api_key_repo

    def handle(self, command: CreateApiKeyCommand) -> None:
        count = self.api_key_repo.count_active_by_user(command.user_id)
        if count >= MAX_ACTIVE_KEYS:
            raise MaxApiKeysReachedError(
                f"Maximum {MAX_ACTIVE_KEYS} active API keys allowed"
            )

        api_key = ApiKey.create(
            user_id=command.user_id,
            key_hash=command.key_hash,
            name=command.name,
            id=command.id,
        )
        self.api_key_repo.save(api_key)
