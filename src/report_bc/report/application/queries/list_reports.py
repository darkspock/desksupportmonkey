from dataclasses import dataclass

from src.framework.application.query_bus import Query, QueryHandler
from src.report_bc.report.domain.entities import Report
from src.report_bc.report.domain.repository import ReportRepositoryInterface


@dataclass
class ListReportsQuery(Query):
    company_id: str
    page: int = 1
    page_size: int = 20


class ListReportsQueryHandler(QueryHandler[ListReportsQuery, tuple[list[Report], int]]):
    def __init__(self, report_repo: ReportRepositoryInterface):
        self.report_repo = report_repo

    def handle(self, query: ListReportsQuery) -> tuple[list[Report], int]:
        return self.report_repo.find_all(
            company_id=query.company_id,
            page=query.page,
            page_size=query.page_size,
        )
