from datetime import datetime, timedelta
from unittest.mock import MagicMock

from src.asset_bc.asset.application.queries.cmdb_dashboard import (
    CMDBDashboardDto,
    GetCMDBDashboardQuery,
    GetCMDBDashboardQueryHandler,
    MostDependedAssetDto,
    OverdueBIAReviewDto,
)

COMPANY_ID = "comp-001"


def _build_handler(
    asset_repo: MagicMock | None = None,
    ci_repo: MagicMock | None = None,
) -> GetCMDBDashboardQueryHandler:
    return GetCMDBDashboardQueryHandler(
        asset_repo=asset_repo or MagicMock(),
        ci_repo=ci_repo or MagicMock(),
    )


def _configure_repos(
    asset_repo: MagicMock,
    ci_repo: MagicMock,
    *,
    criticality: dict[str, int] | None = None,
    orphan_count: int = 0,
    bia_stats: dict | None = None,
    total_relationships: int = 0,
    relationships_by_type: dict[str, int] | None = None,
    most_depended_raw: list[dict] | None = None,
    overdue_raw: list[dict] | None = None,
) -> None:
    asset_repo.count_by_criticality.return_value = criticality or {}
    asset_repo.count_orphan_critical_assets.return_value = orphan_count
    asset_repo.bia_coverage_stats.return_value = bia_stats or {
        "total_critical_high": 0,
        "has_bia": 0,
        "coverage_pct": 0.0,
    }
    asset_repo.find_overdue_bia_reviews.return_value = overdue_raw or []

    ci_repo.count_all.return_value = total_relationships
    ci_repo.count_by_type.return_value = relationships_by_type or {}
    ci_repo.count_incoming_by_asset.return_value = most_depended_raw or []


def test_all_metrics_populated():
    """All 7 repo calls return data; DTO is assembled correctly."""
    asset_repo = MagicMock()
    ci_repo = MagicMock()

    old_date = datetime(2024, 6, 1, 12, 0, 0)

    _configure_repos(
        asset_repo,
        ci_repo,
        criticality={"critical": 5, "high": 10, "medium": 20, "low": 15},
        orphan_count=3,
        bia_stats={"total_critical_high": 15, "has_bia": 9, "coverage_pct": 60.0},
        total_relationships=42,
        relationships_by_type={"depends_on": 20, "runs_on": 15, "connected_to": 7},
        most_depended_raw=[
            {"asset_id": "a1", "asset_name": "DB Server", "asset_tag": "SRV-001", "count": 12},
            {"asset_id": "a2", "asset_name": "Switch Core", "asset_tag": None, "count": 8},
        ],
        overdue_raw=[
            {
                "id": "a3",
                "name": "Firewall",
                "asset_tag": "FW-001",
                "criticality": "critical",
                "bia_reviewed_at": old_date,
            },
        ],
    )

    handler = _build_handler(asset_repo, ci_repo)
    result = handler.handle(GetCMDBDashboardQuery(company_id=COMPANY_ID))

    assert isinstance(result, CMDBDashboardDto)
    assert result.criticality_distribution == {
        "critical": 5, "high": 10, "medium": 20, "low": 15,
    }
    assert result.orphan_critical_count == 3
    assert result.bia_total_critical_high == 15
    assert result.bia_has_coverage == 9
    assert result.bia_coverage_pct == 60.0
    assert result.total_relationships == 42
    assert result.relationships_by_type == {
        "depends_on": 20, "runs_on": 15, "connected_to": 7,
    }

    # MostDependedAssetDto mapping
    assert len(result.most_depended_upon) == 2
    first = result.most_depended_upon[0]
    assert isinstance(first, MostDependedAssetDto)
    assert first.asset_id == "a1"
    assert first.asset_name == "DB Server"
    assert first.asset_tag == "SRV-001"
    assert first.incoming_count == 12
    second = result.most_depended_upon[1]
    assert second.asset_tag is None
    assert second.incoming_count == 8

    # OverdueBIAReviewDto mapping
    assert len(result.overdue_bia_reviews) == 1
    overdue = result.overdue_bia_reviews[0]
    assert isinstance(overdue, OverdueBIAReviewDto)
    assert overdue.asset_id == "a3"
    assert overdue.asset_name == "Firewall"
    assert overdue.asset_tag == "FW-001"
    assert overdue.criticality == "critical"
    assert overdue.bia_reviewed_at == old_date

    # Verify all repo methods were called with company_id
    asset_repo.count_by_criticality.assert_called_once_with(COMPANY_ID)
    asset_repo.count_orphan_critical_assets.assert_called_once_with(COMPANY_ID)
    asset_repo.bia_coverage_stats.assert_called_once_with(COMPANY_ID)
    asset_repo.find_overdue_bia_reviews.assert_called_once_with(COMPANY_ID, months=6)
    ci_repo.count_all.assert_called_once_with(COMPANY_ID)
    ci_repo.count_by_type.assert_called_once_with(COMPANY_ID)
    ci_repo.count_incoming_by_asset.assert_called_once_with(COMPANY_ID)


def test_empty_company_returns_zeros():
    """A company with no assets yields zero counts, empty lists, 0.0 coverage."""
    asset_repo = MagicMock()
    ci_repo = MagicMock()

    _configure_repos(asset_repo, ci_repo)  # all defaults are empty/zero

    handler = _build_handler(asset_repo, ci_repo)
    result = handler.handle(GetCMDBDashboardQuery(company_id=COMPANY_ID))

    assert result.criticality_distribution == {}
    assert result.orphan_critical_count == 0
    assert result.bia_total_critical_high == 0
    assert result.bia_has_coverage == 0
    assert result.bia_coverage_pct == 0.0
    assert result.total_relationships == 0
    assert result.relationships_by_type == {}
    assert result.most_depended_upon == []
    assert result.overdue_bia_reviews == []


def test_orphan_critical_asset_counted():
    """A critical asset with no CI relationships is counted as orphan."""
    asset_repo = MagicMock()
    ci_repo = MagicMock()

    _configure_repos(
        asset_repo,
        ci_repo,
        criticality={"critical": 4, "high": 6},
        orphan_count=2,
        bia_stats={"total_critical_high": 10, "has_bia": 5, "coverage_pct": 50.0},
        total_relationships=10,
    )

    handler = _build_handler(asset_repo, ci_repo)
    result = handler.handle(GetCMDBDashboardQuery(company_id=COMPANY_ID))

    assert result.orphan_critical_count == 2
    assert result.criticality_distribution["critical"] == 4


def test_bia_coverage_percentage_computed():
    """BIA coverage_pct is correctly passed from repo stats (has_bia / total * 100)."""
    asset_repo = MagicMock()
    ci_repo = MagicMock()

    _configure_repos(
        asset_repo,
        ci_repo,
        criticality={"critical": 3, "high": 7},
        bia_stats={"total_critical_high": 10, "has_bia": 4, "coverage_pct": 40.0},
    )

    handler = _build_handler(asset_repo, ci_repo)
    result = handler.handle(GetCMDBDashboardQuery(company_id=COMPANY_ID))

    assert result.bia_total_critical_high == 10
    assert result.bia_has_coverage == 4
    assert result.bia_coverage_pct == 40.0

    # Edge case: zero critical/high assets yields 0.0% coverage
    _configure_repos(
        asset_repo,
        ci_repo,
        bia_stats={"total_critical_high": 0, "has_bia": 0, "coverage_pct": 0.0},
    )

    result_zero = handler.handle(GetCMDBDashboardQuery(company_id=COMPANY_ID))

    assert result_zero.bia_total_critical_high == 0
    assert result_zero.bia_has_coverage == 0
    assert result_zero.bia_coverage_pct == 0.0


def test_overdue_bia_reviews_includes_null_and_old_dates():
    """Both null bia_reviewed_at and old dates appear in overdue results."""
    asset_repo = MagicMock()
    ci_repo = MagicMock()

    old_date = datetime(2024, 1, 15, 10, 0, 0)

    _configure_repos(
        asset_repo,
        ci_repo,
        criticality={"critical": 2, "high": 3},
        bia_stats={"total_critical_high": 5, "has_bia": 2, "coverage_pct": 40.0},
        overdue_raw=[
            {
                "id": "asset-null",
                "name": "Core Router",
                "asset_tag": "RTR-001",
                "criticality": "critical",
                "bia_reviewed_at": None,
            },
            {
                "id": "asset-old",
                "name": "Mail Server",
                "asset_tag": "SRV-010",
                "criticality": "high",
                "bia_reviewed_at": old_date,
            },
            {
                "id": "asset-no-tag",
                "name": "Legacy Switch",
                "criticality": "critical",
                "bia_reviewed_at": None,
            },
        ],
    )

    handler = _build_handler(asset_repo, ci_repo)
    result = handler.handle(GetCMDBDashboardQuery(company_id=COMPANY_ID))

    assert len(result.overdue_bia_reviews) == 3

    # Null bia_reviewed_at
    null_review = result.overdue_bia_reviews[0]
    assert null_review.asset_id == "asset-null"
    assert null_review.asset_name == "Core Router"
    assert null_review.asset_tag == "RTR-001"
    assert null_review.criticality == "critical"
    assert null_review.bia_reviewed_at is None

    # Old date
    old_review = result.overdue_bia_reviews[1]
    assert old_review.asset_id == "asset-old"
    assert old_review.asset_name == "Mail Server"
    assert old_review.asset_tag == "SRV-010"
    assert old_review.criticality == "high"
    assert old_review.bia_reviewed_at == old_date

    # Missing asset_tag key defaults to None via .get()
    no_tag_review = result.overdue_bia_reviews[2]
    assert no_tag_review.asset_id == "asset-no-tag"
    assert no_tag_review.asset_tag is None
    assert no_tag_review.bia_reviewed_at is None
