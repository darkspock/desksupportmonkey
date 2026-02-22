from dataclasses import dataclass

from src.framework.application.query_bus import Query, QueryHandler


@dataclass
class GetOAuthProvidersQuery(Query):
    pass


class GetOAuthProvidersHandler(QueryHandler["GetOAuthProvidersQuery", dict]):
    def __init__(self, google_client_id: str, microsoft_client_id: str):
        self.google_client_id = google_client_id
        self.microsoft_client_id = microsoft_client_id

    def handle(self, query: "GetOAuthProvidersQuery") -> dict:
        return {
            "google": bool(self.google_client_id),
            "microsoft": bool(self.microsoft_client_id),
        }
