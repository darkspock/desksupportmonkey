from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Any, Dict, Type


class Query(ABC):
    """Base class for all queries."""
    pass


TQuery = TypeVar('TQuery', bound=Query)
TResult = TypeVar('TResult')


class QueryHandler(ABC, Generic[TQuery, TResult]):
    """Base class for all query handlers."""

    @abstractmethod
    def handle(self, query: TQuery) -> TResult:
        pass


class QueryBus:
    """Query bus that resolves handlers by convention."""

    def __init__(self, container: Any) -> None:
        """Initialize QueryBus with container dependency.

        Args:
            container: Container instance for resolving handlers.
        """
        self.container = container
        self._handlers_cache: Dict[Type[Query], Any] = {}

    def query(self, query: Any) -> Any:
        """Execute a query by automatically finding the handler by naming convention."""
        query_type = type(query)

        # Cache handler to avoid repeated lookups
        if query_type in self._handlers_cache:
            handler_instance = self._handlers_cache[query_type]()
            return handler_instance.handle(query)

        # Find handler by convention: GetUserQuery -> get_user_query_handler
        handler_name = f"{query_type.__name__}Handler"
        handler_provider_name = self._camel_to_snake(handler_name)

        handler_provider = getattr(self.container, handler_provider_name)
        self._handlers_cache[query_type] = handler_provider
        handler_instance = handler_provider()
        return handler_instance.handle(query)

    @staticmethod
    def _camel_to_snake(name: str) -> str:
        """Convert CamelCase to snake_case."""
        import re
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
