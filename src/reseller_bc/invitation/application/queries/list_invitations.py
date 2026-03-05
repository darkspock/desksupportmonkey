from dataclasses import dataclass

from src.framework.application.query_bus import Query, QueryHandler
from src.reseller_bc.invitation.application.dtos import InvitationDto, InvitationListDto
from src.reseller_bc.invitation.domain.repository import ResellerInvitationRepositoryInterface


@dataclass
class ListInvitationsQuery(Query):
    reseller_id: str
    offset: int = 0
    limit: int = 50


class ListInvitationsQueryHandler(QueryHandler[ListInvitationsQuery, InvitationListDto]):
    def __init__(self, invitation_repo: ResellerInvitationRepositoryInterface):
        self.invitation_repo = invitation_repo

    def handle(self, query: ListInvitationsQuery) -> InvitationListDto:
        invitations = self.invitation_repo.find_by_reseller_id(
            query.reseller_id, query.offset, query.limit,
        )
        total = self.invitation_repo.count_by_reseller_id(query.reseller_id)
        return InvitationListDto(
            items=[InvitationDto.from_entity(inv) for inv in invitations],
            total=total,
        )
