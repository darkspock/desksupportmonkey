"""Application service for switching a user's active company."""

from dataclasses import dataclass

from core.jwt import JWTService
from src.auth_bc.company_user.domain.entities import (
    MembershipDeactivatedError,
    MembershipNotFoundError,
)
from src.auth_bc.company_user.domain.repository import CompanyUserRepositoryInterface
from src.auth_bc.user.domain.repository import UserRepositoryInterface


@dataclass
class SwitchCompanyRequest:
    user_id: str
    target_company_id: str


class SwitchCompanyService:
    """Validates membership, copies to user row, issues new JWT."""

    def __init__(
        self,
        user_repo: UserRepositoryInterface,
        company_user_repo: CompanyUserRepositoryInterface,
        jwt_service: JWTService,
    ):
        self.user_repo = user_repo
        self.company_user_repo = company_user_repo
        self.jwt_service = jwt_service

    def handle(self, request: SwitchCompanyRequest) -> str:
        """Switch user's active company. Returns new JWT access_token."""
        # 1. Get user
        user = self.user_repo.find_by_id(request.user_id)
        if user is None:
            raise MembershipNotFoundError("User not found")

        # 2. Find membership in target company
        membership = self.company_user_repo.find_by_user_and_company(
            request.user_id, request.target_company_id
        )
        if membership is None:
            raise MembershipNotFoundError(
                "No membership found in target company"
            )
        if not membership.is_active:
            raise MembershipDeactivatedError(
                "Your membership in this company is deactivated"
            )

        # 3. Copy membership data to user row
        user.company_id = request.target_company_id
        user.role = membership.role
        user.department_id = membership.department_id
        user.employee_role_id = membership.employee_role_id
        self.user_repo.save(user)

        # 4. Issue new JWT with updated company_id
        return self.jwt_service.create_token(
            user_id=user.id,
            company_id=user.company_id,
            role=user.role.value,
        )
