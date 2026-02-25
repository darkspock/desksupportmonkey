from unittest.mock import MagicMock

from src.company_bc.nav_config.application.queries.get_nav_config import (
    GetNavConfigQuery,
    GetNavConfigQueryHandler,
)
from src.company_bc.nav_config.domain.entities import CompanyNavConfig


class TestGetNavConfigQuery:
    def test_returns_config_when_found(self):
        config = CompanyNavConfig.create(
            company_id="comp123",
            hidden_nav_items={"employee": ["/my/shipments"]},
        )
        repo = MagicMock()
        repo.find_by_company.return_value = config
        handler = GetNavConfigQueryHandler(nav_config_repo=repo)

        result = handler.handle(
            GetNavConfigQuery(company_id="comp123")
        )

        assert result is not None
        assert result.company_id == "comp123"
        assert result.hidden_nav_items == {"employee": ["/my/shipments"]}
        repo.find_by_company.assert_called_once_with("comp123")

    def test_returns_none_when_not_found(self):
        repo = MagicMock()
        repo.find_by_company.return_value = None
        handler = GetNavConfigQueryHandler(nav_config_repo=repo)

        result = handler.handle(
            GetNavConfigQuery(company_id="comp999")
        )

        assert result is None
        repo.find_by_company.assert_called_once_with("comp999")
