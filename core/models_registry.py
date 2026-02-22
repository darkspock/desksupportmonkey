"""
SQLAlchemy Models Registry

This module imports all SQLAlchemy models to ensure they're loaded
before mapper configuration. This prevents "failed to locate name"
errors when models have bidirectional relationships.

Import this module early in the application startup to ensure
all models are registered with SQLAlchemy's mapper.
"""

# Company BC
from src.company_bc.company.infrastructure.models import CompanyModel  # noqa: F401
from src.company_bc.company.infrastructure.models import CompanyEmailDomainModel  # noqa: F401
from src.company_bc.company.infrastructure.models import ProcessedStripeEventModel  # noqa: F401

# Department
from src.company_bc.department.infrastructure.models import DepartmentModel  # noqa: F401

# Auth BC
from src.auth_bc.user.infrastructure.models import UserModel  # noqa: F401
from src.auth_bc.magic_link.infrastructure.models import MagicLinkModel  # noqa: F401

# Asset BC
from src.asset_bc.asset.infrastructure.models import AssetModel  # noqa: F401
from src.asset_bc.asset.infrastructure.models import AssetEventModel  # noqa: F401

# Request BC
from src.request_bc.request.infrastructure.models import ServiceRequestModel  # noqa: F401
from src.request_bc.request.infrastructure.models import RequestEventModel  # noqa: F401
from src.request_bc.request.infrastructure.models import RequestCommentModel  # noqa: F401
from src.request_bc.request.infrastructure.models import RequestNoteModel  # noqa: F401

# Notification BC
from src.notification_bc.notification.infrastructure.models import NotificationModel  # noqa: F401

# Report BC
from src.report_bc.report.infrastructure.models import ReportModel  # noqa: F401

__all__ = [
    "CompanyModel",
    "CompanyEmailDomainModel",
    "ProcessedStripeEventModel",
    "DepartmentModel",
    "UserModel",
    "MagicLinkModel",
    "AssetModel",
    "AssetEventModel",
    "ServiceRequestModel",
    "RequestEventModel",
    "RequestCommentModel",
    "RequestNoteModel",
    "NotificationModel",
    "ReportModel",
]
