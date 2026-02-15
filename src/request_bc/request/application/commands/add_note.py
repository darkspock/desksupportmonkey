from dataclasses import dataclass

from src.request_bc.request.domain.entities import RequestEvent, RequestNote
from src.request_bc.request.domain.repository import RequestRepositoryInterface


class RequestNotFoundError(Exception):
    pass


@dataclass
class AddNoteCommand:
    request_id: str
    company_id: str
    author_id: str
    body: str


class AddNoteCommandHandler:
    def __init__(self, request_repo: RequestRepositoryInterface):
        self.request_repo = request_repo

    def handle(self, command: AddNoteCommand) -> RequestNote:
        request = self.request_repo.find_by_id(command.request_id, command.company_id)
        if not request:
            raise RequestNotFoundError(f"Request '{command.request_id}' not found")

        note = RequestNote.create(
            request_id=command.request_id,
            author_id=command.author_id,
            body=command.body,
        )

        note = self.request_repo.save_note(note)

        event = RequestEvent.create(
            request_id=command.request_id,
            event_type="note_added",
            data={"note_id": note.id, "author_id": command.author_id},
            performed_by=command.author_id,
        )
        self.request_repo.save_event(event)

        return note
