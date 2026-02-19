from abc import ABC, abstractmethod
from typing import Optional

from src.mcp_bc.server.domain.entities import ApiKey


class ApiKeyRepositoryInterface(ABC):

    @abstractmethod
    def save(self, api_key: ApiKey) -> ApiKey: ...

    @abstractmethod
    def find_by_id(self, key_id: str, user_id: str) -> Optional[ApiKey]: ...

    @abstractmethod
    def find_all_by_user(self, user_id: str) -> list[ApiKey]: ...

    @abstractmethod
    def count_active_by_user(self, user_id: str) -> int: ...

    @abstractmethod
    def find_active_by_hash(self, key_hash: str) -> Optional[ApiKey]: ...

    @abstractmethod
    def find_all_active(self) -> list[ApiKey]: ...

    @abstractmethod
    def update_last_used(self, key_id: str) -> None: ...
