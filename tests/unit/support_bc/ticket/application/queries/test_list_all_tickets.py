from unittest.mock import MagicMock

from src.support_bc.ticket.application.queries.list_all_tickets import (
    ListAllTicketsQuery,
    ListAllTicketsQueryHandler,
)


class TestListAllTicketsQueryHandler:
    def test_passes_all_params_to_repo(self):
        repo = MagicMock()
        repo.find_all.return_value = ([], 0)
        handler = ListAllTicketsQueryHandler(ticket_repo=repo)

        handler.handle(
            ListAllTicketsQuery(
                page=2,
                page_size=10,
                status="open",
                category="bug_report",
                priority="high",
                search="test",
                company_id="comp-123",
                sort_by="created_at",
                sort_order="asc",
            )
        )

        repo.find_all.assert_called_once_with(
            page=2,
            page_size=10,
            status="open",
            category="bug_report",
            priority="high",
            search="test",
            company_id="comp-123",
            sort_by="created_at",
            sort_order="asc",
        )

    def test_passes_none_defaults(self):
        repo = MagicMock()
        repo.find_all.return_value = ([], 0)
        handler = ListAllTicketsQueryHandler(ticket_repo=repo)

        handler.handle(ListAllTicketsQuery())

        repo.find_all.assert_called_once_with(
            page=1,
            page_size=20,
            status=None,
            category=None,
            priority=None,
            search=None,
            company_id=None,
            sort_by=None,
            sort_order=None,
        )

    def test_returns_repo_result(self):
        ticket_mock = MagicMock()
        repo = MagicMock()
        repo.find_all.return_value = ([ticket_mock], 1)
        handler = ListAllTicketsQueryHandler(ticket_repo=repo)

        tickets, total = handler.handle(ListAllTicketsQuery())

        assert tickets == [ticket_mock]
        assert total == 1
