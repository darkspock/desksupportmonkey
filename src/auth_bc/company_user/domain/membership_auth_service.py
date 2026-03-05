import logging

from src.auth_bc.company_lookup.domain.service import CompanyLookupInterface
from src.auth_bc.company_user.domain.entities import (
    CompanyUser,
    MembershipDeactivatedError,
    MembershipNotAllowedError,
)
from src.auth_bc.company_user.domain.repository import CompanyUserRepositoryInterface
from src.auth_bc.user.domain.entities import User
from src.auth_bc.user.domain.enums import UserRole
from src.auth_bc.user.domain.repository import UserRepositoryInterface

logger = logging.getLogger(__name__)


class MembershipAuthService:
    """Two-step auth flow: resolve membership and copy to user row."""

    def __init__(
        self,
        company_user_repo: CompanyUserRepositoryInterface,
        company_lookup: CompanyLookupInterface,
        user_repo: UserRepositoryInterface,
    ):
        self.company_user_repo = company_user_repo
        self.company_lookup = company_lookup
        self.user_repo = user_repo

    def resolve_membership(self, user: User, company_id: str, auth_mode: str) -> User:
        """
        Given an authenticated user and target company_id:
        1. Find CompanyUser for (user_id, company_id)
        2. If found + active -> copy membership data to user row
        3. If found + inactive -> raise MembershipDeactivatedError
        4. If not found + domain mode -> check email domain -> auto-create CompanyUser -> copy
        5. If not found + membership_only -> raise MembershipNotAllowedError
        Returns the updated user (user row reflects membership data).
        """
        membership = self.company_user_repo.find_by_user_and_company(user.id, company_id)

        if membership is not None:
            if not membership.is_active:
                raise MembershipDeactivatedError(
                    "Your account in this company is deactivated"
                )
            self._copy_membership_to_user(user, membership, company_id)
            return user

        # No membership exists
        if auth_mode == "membership_only":
            raise MembershipNotAllowedError(
                "You don't have access to this company"
            )

        # Domain mode: check email domain, auto-create membership
        allowed = self.company_lookup.is_email_allowed_in_company(user.email, company_id)
        if not allowed:
            raise MembershipNotAllowedError(
                "Your email domain is not allowed for this company"
            )

        membership = CompanyUser.create(
            user_id=user.id,
            company_id=company_id,
            role=UserRole.EMPLOYEE,
        )
        self.company_user_repo.save(membership)
        self._copy_membership_to_user(user, membership, company_id)
        logger.info(
            "Auto-created membership for user %s in company %s",
            user.id,
            company_id,
        )
        return user

    def _copy_membership_to_user(
        self, user: User, membership: CompanyUser, company_id: str
    ) -> None:
        """Copy membership data to user row (copy-on-switch semantics)."""
        user.company_id = company_id
        user.role = membership.role
        user.department_id = membership.department_id
        user.employee_role_id = membership.employee_role_id
        user.is_active = membership.is_active
        self.user_repo.save(user)
