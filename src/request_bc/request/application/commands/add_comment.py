from dataclasses import dataclass
from typing import Optional

from src.framework.application.command_bus import Command, CommandHandler
from src.request_bc.request.domain.entities import RequestComment, RequestEvent
from src.request_bc.request.domain.repository import RequestRepositoryInterface


class RequestNotFoundError(Exception):
    pass


@dataclass
class AddCommentCommand(Command):
    request_id: str
    company_id: str
    author_id: str
    body: str
    id: Optional[str] = None


class AddCommentCommandHandler(CommandHandler[AddCommentCommand]):
    def __init__(self, request_repo: RequestRepositoryInterface):
        self.request_repo = request_repo

    def handle(self, command: AddCommentCommand) -> None:
        request = self.request_repo.find_by_id(command.request_id, command.company_id)
        if not request:
            raise RequestNotFoundError(f"Request '{command.request_id}' not found")

        comment = RequestComment.create(
            request_id=command.request_id,
            author_id=command.author_id,
            body=command.body,
            id=command.id,
        )

        self.request_repo.save_comment(comment)

        event = RequestEvent.create(
            request_id=command.request_id,
            event_type="comment_added",
            data={"comment_id": comment.id, "author_id": command.author_id},
            performed_by=command.author_id,
        )
        self.request_repo.save_event(event)
