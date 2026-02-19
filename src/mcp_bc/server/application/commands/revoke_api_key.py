from dataclasses import dataclass

from src.framework.application.command_bus import Command, CommandHandler
from src.mcp_bc.server.domain.repository import ApiKeyRepositoryInterface


class ApiKeyNotFoundError(Exception):
    pass


@dataclass
class RevokeApiKeyCommand(Command):
    key_id: str
    user_id: str


class RevokeApiKeyCommandHandler(CommandHandler[RevokeApiKeyCommand]):
    def __init__(self, api_key_repo: ApiKeyRepositoryInterface):
        self.api_key_repo = api_key_repo

    def handle(self, command: RevokeApiKeyCommand) -> None:
        api_key = self.api_key_repo.find_by_id(command.key_id, command.user_id)
        if not api_key:
            raise ApiKeyNotFoundError(f"API key '{command.key_id}' not found")
        api_key.revoke()
        self.api_key_repo.save(api_key)
