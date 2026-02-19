from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from src.request_bc.request.application.services.request_classifier import (
        ClassificationResult,
    )


class UserLookup(ABC):
    """Port for looking up users from request_bc.

    Satisfied by auth_bc's UserRepository at the router level.
    """

    @abstractmethod
    def find_by_id_and_company(self, user_id: str, company_id: str) -> Optional[Any]:
        """Find a user by ID scoped to a company. Returns None if not found.

        The returned object must have `is_active: bool`.
        """
        ...


class RequestClassifierPort(ABC):
    """Port for AI-based request classification."""

    @abstractmethod
    def classify(
        self,
        title: str,
        description: str,
        valid_types: dict[str, list[str]],
        custom_instructions: Optional[str] = None,
    ) -> Optional[ClassificationResult]:
        """Classify a request. Returns None on any failure."""
        ...
