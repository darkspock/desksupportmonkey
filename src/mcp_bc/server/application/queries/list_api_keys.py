from dataclasses import dataclass

from src.framework.application.query_bus import Query, QueryHandler
from src.mcp_bc.server.domain.entities import ApiKey
from src.mcp_bc.server.domain.repository import ApiKeyRepositoryInterface


@dataclass
class ListApiKeysQuery(Query):
    user_id: str


class ListApiKeysQueryHandler(QueryHandler[ListApiKeysQuery, list[ApiKey]]):
    def __init__(self, api_key_repo: ApiKeyRepositoryInterface):
        self.api_key_repo = api_key_repo

    def handle(self, query: ListApiKeysQuery) -> list[ApiKey]:
        return self.api_key_repo.find_all_by_user(query.user_id)
