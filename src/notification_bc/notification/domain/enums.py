from enum import Enum


class EventType(str, Enum):
    REQUEST_CREATED = "request.created"
    REQUEST_STATUS_CHANGED = "request.status_changed"
    REQUEST_ASSIGNED = "request.assigned"
    REQUEST_PRIORITY_CHANGED = "request.priority_changed"
    REQUEST_COMMENT_ADDED = "request.comment_added"
    REQUEST_NOTE_ADDED = "request.note_added"
