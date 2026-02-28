from dataclasses import dataclass

from src.asset_bc.asset.domain.entities import CIRelationship
from src.asset_bc.asset.domain.repository import CIRelationshipRepositoryInterface
from src.framework.application.query_bus import Query, QueryHandler


@dataclass
class ListCIRelationshipsQuery(Query):
    asset_id: str
    company_id: str


class ListCIRelationshipsQueryHandler(QueryHandler[ListCIRelationshipsQuery, list[CIRelationship]]):
    def __init__(self, ci_repo: CIRelationshipRepositoryInterface):
        self.ci_repo = ci_repo

    def handle(self, query: ListCIRelationshipsQuery) -> list[CIRelationship]:
        return self.ci_repo.find_by_asset(query.asset_id, query.company_id)
