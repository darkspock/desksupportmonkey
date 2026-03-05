from src.reseller_bc.client.application.dtos import (
    DemoAccountCreatedDto,
    ResellerClientDto,
    ResellerClientListDto,
)
from src.reseller_bc.commission.application.dtos import CommissionDto, CommissionListDto
from src.reseller_bc.invitation.application.dtos import InvitationDto, InvitationListDto
from src.reseller_bc.payout.application.dtos import PayoutDto, PayoutListDto
from src.reseller_bc.reseller.application.dtos import (
    ResellerDashboardDto,
    ResellerDto,
    ResellerListDto,
)
from adapters.http.api.reseller.schemas import (
    CommissionListResponse,
    CommissionResponse,
    DemoAccountCreatedResponse,
    InvitationListResponse,
    InvitationResponse,
    PayoutListResponse,
    PayoutResponse,
    ResellerClientListResponse,
    ResellerClientResponse,
    ResellerDashboardResponse,
    ResellerListResponse,
    ResellerResponse,
)


class ResellerMapper:
    @staticmethod
    def dto_to_response(dto: ResellerDto) -> ResellerResponse:
        return ResellerResponse(
            id=dto.id,
            email=dto.email,
            name=dto.name,
            avatar_url=dto.avatar_url,
            company_name=dto.company_name,
            tax_id=dto.tax_id,
            commission_pct=dto.commission_pct,
            min_payout_cents=dto.min_payout_cents,
            referral_code=dto.referral_code,
            status=dto.status,
            created_at=dto.created_at.isoformat() if dto.created_at else "",
            updated_at=dto.updated_at.isoformat() if dto.updated_at else None,
        )

    @staticmethod
    def dto_to_dashboard_response(dto: ResellerDashboardDto) -> ResellerDashboardResponse:
        return ResellerDashboardResponse(
            reseller_id=dto.reseller_id,
            name=dto.name,
            referral_code=dto.referral_code,
            status=dto.status,
            client_count=dto.client_count,
            total_commissions_cents=dto.total_commissions_cents,
            available_balance_cents=dto.available_balance_cents,
            pending_payout_cents=dto.pending_payout_cents,
        )

    @staticmethod
    def dto_to_list_response(dto: ResellerListDto) -> ResellerListResponse:
        return ResellerListResponse(
            items=[ResellerMapper.dto_to_response(item) for item in dto.items],
            total=dto.total,
        )


class ResellerClientMapper:
    @staticmethod
    def dto_to_response(dto: ResellerClientDto) -> ResellerClientResponse:
        return ResellerClientResponse(
            id=dto.id,
            reseller_id=dto.reseller_id,
            company_id=dto.company_id,
            company_name=dto.company_name,
            source=dto.source,
            is_demo=dto.is_demo,
            demo_expires_at=dto.demo_expires_at.isoformat() if dto.demo_expires_at else None,
            plan=dto.plan,
            company_status=dto.company_status,
            created_at=dto.created_at.isoformat() if dto.created_at else None,
        )

    @staticmethod
    def dto_to_list_response(dto: ResellerClientListDto) -> ResellerClientListResponse:
        return ResellerClientListResponse(
            items=[ResellerClientMapper.dto_to_response(item) for item in dto.items],
            total=dto.total,
        )

    @staticmethod
    def demo_dto_to_response(dto: DemoAccountCreatedDto) -> DemoAccountCreatedResponse:
        return DemoAccountCreatedResponse(
            client_id=dto.client_id,
            company_id=dto.company_id,
            company_name=dto.company_name,
            admin_email=dto.admin_email,
            admin_password=dto.admin_password,
        )


class InvitationMapper:
    @staticmethod
    def dto_to_response(dto: InvitationDto) -> InvitationResponse:
        return InvitationResponse(
            id=dto.id,
            reseller_id=dto.reseller_id,
            email=dto.email,
            status=dto.status,
            expires_at=dto.expires_at.isoformat() if dto.expires_at else "",
            created_at=dto.created_at.isoformat() if dto.created_at else None,
        )

    @staticmethod
    def dto_to_list_response(dto: InvitationListDto) -> InvitationListResponse:
        return InvitationListResponse(
            items=[InvitationMapper.dto_to_response(item) for item in dto.items],
            total=dto.total,
        )


class CommissionMapper:
    @staticmethod
    def dto_to_response(dto: CommissionDto) -> CommissionResponse:
        return CommissionResponse(
            id=dto.id,
            reseller_id=dto.reseller_id,
            company_id=dto.company_id,
            company_name=dto.company_name,
            payment_amount_cents=dto.payment_amount_cents,
            commission_pct=dto.commission_pct,
            commission_amount_cents=dto.commission_amount_cents,
            period_start=dto.period_start.isoformat() if dto.period_start else None,
            period_end=dto.period_end.isoformat() if dto.period_end else None,
            status=dto.status,
            created_at=dto.created_at.isoformat() if dto.created_at else None,
        )

    @staticmethod
    def dto_to_list_response(dto: CommissionListDto) -> CommissionListResponse:
        return CommissionListResponse(
            items=[CommissionMapper.dto_to_response(item) for item in dto.items],
            total=dto.total,
        )


class PayoutMapper:
    @staticmethod
    def dto_to_response(dto: PayoutDto) -> PayoutResponse:
        return PayoutResponse(
            id=dto.id,
            reseller_id=dto.reseller_id,
            reseller_name=dto.reseller_name,
            amount_cents=dto.amount_cents,
            status=dto.status,
            requested_at=dto.requested_at.isoformat() if dto.requested_at else None,
            processed_at=dto.processed_at.isoformat() if dto.processed_at else None,
            processed_by=dto.processed_by,
            payment_reference=dto.payment_reference,
            notes=dto.notes,
        )

    @staticmethod
    def dto_to_list_response(dto: PayoutListDto) -> PayoutListResponse:
        return PayoutListResponse(
            items=[PayoutMapper.dto_to_response(item) for item in dto.items],
            total=dto.total,
        )
