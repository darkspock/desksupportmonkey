from core.jwt import JWTService
from core.password import PasswordService
from src.reseller_bc.reseller.domain.enums import ResellerStatus
from src.reseller_bc.reseller.domain.exceptions import (
    ResellerDeactivatedException,
    ResellerInvalidPasswordException,
    ResellerNotRegisteredException,
    ResellerPendingApprovalException,
)
from src.reseller_bc.reseller.domain.repository import ResellerRepositoryInterface


class ResellerPasswordLoginService:
    def __init__(
        self,
        repo: ResellerRepositoryInterface,
        password_service: PasswordService,
        jwt_service: JWTService,
    ):
        self.repo = repo
        self.password_service = password_service
        self.jwt_service = jwt_service

    def login(self, email: str, password: str) -> str:
        reseller = self.repo.find_by_email(email)
        if reseller is None:
            raise ResellerNotRegisteredException(email)

        if not reseller.has_password:
            raise ResellerInvalidPasswordException(
                "This account uses OAuth login. Please sign in with Google or Microsoft."
            )

        assert reseller.password_hash is not None  # guaranteed by has_password
        if not self.password_service.verify_password(password, reseller.password_hash):
            raise ResellerInvalidPasswordException("Invalid email or password")

        if reseller.status == ResellerStatus.PENDING:
            raise ResellerPendingApprovalException()

        if reseller.status == ResellerStatus.DEACTIVATED:
            raise ResellerDeactivatedException(reseller.id)

        return self.jwt_service.create_token(
            user_id=reseller.id,
            company_id=None,
            role="reseller",
            type="reseller",
        )
