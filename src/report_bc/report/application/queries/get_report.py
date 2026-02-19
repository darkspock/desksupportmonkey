from dataclasses import dataclass

from src.framework.application.query_bus import Query, QueryHandler
from src.report_bc.report.domain.entities import Report
from src.report_bc.report.domain.repository import ReportRepositoryInterface


class ReportNotFoundError(Exception):
    pass


@dataclass
class GetReportQuery(Query):
    report_id: str
    company_id: str


class GetReportQueryHandler(QueryHandler[GetReportQuery, Report]):
    def __init__(self, report_repo: ReportRepositoryInterface):
        self.report_repo = report_repo

    def handle(self, query: GetReportQuery) -> Report:
        report = self.report_repo.find_by_id(query.report_id, query.company_id)
        if not report:
            raise ReportNotFoundError(f"Report {query.report_id} not found")
        return report
