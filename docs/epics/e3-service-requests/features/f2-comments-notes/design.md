# Design: F2 - Comments + Internal Notes

**Feature:** [requirements.md](requirements.md)
**Date:** 2026-02-15

---

## Architecture Overview

F2 adds comment and note commands/queries on top of F0's entities and models. No new migrations needed (tables already created in F0).

```
NEW FILES:
src/request_bc/request/application/commands/add_comment.py
src/request_bc/request/application/commands/add_note.py
src/request_bc/request/application/queries/list_comments.py
src/request_bc/request/application/queries/list_notes.py

MODIFIED FILES:
src/request_bc/request/infrastructure/repository.py    # Implement comment/note methods
adapters/http/api/requests/routers.py                  # Add comment/note endpoints
adapters/http/api/requests/schemas.py                  # Add comment/note schemas
```

---

## Domain Layer

No new entities. Uses RequestComment, RequestNote, RequestEvent from F0's entities.py.

---

## Infrastructure Layer

### RequestRepository — Implement Comment/Note Methods

```python
def save_comment(self, comment: RequestComment) -> RequestComment:
    model = RequestCommentModel(
        id=comment.id, request_id=comment.request_id,
        author_id=comment.author_id, body=comment.body,
    )
    self.session.add(model)
    self.session.flush()
    self.session.refresh(model)
    return self._comment_to_entity(model)

def find_comments(self, request_id: str) -> list[RequestComment]:
    stmt = select(RequestCommentModel).where(
        RequestCommentModel.request_id == request_id
    ).order_by(RequestCommentModel.created_at.asc())
    models = self.session.execute(stmt).scalars().all()
    return [self._comment_to_entity(m) for m in models]

def save_note(self, note: RequestNote) -> RequestNote:
    # Same pattern as save_comment

def find_notes(self, request_id: str) -> list[RequestNote]:
    # Same pattern as find_comments, using RequestNoteModel
```

Converter methods:
```python
def _comment_to_entity(self, model: RequestCommentModel) -> RequestComment: ...
def _note_to_entity(self, model: RequestNoteModel) -> RequestNote: ...
```

---

## Application Layer

### AddCommentCommand + Handler

```python
@dataclass
class AddCommentCommand:
    request_id: str
    company_id: str
    author_id: str
    body: str
```

Handler:
1. Find request by id + company_id -> RequestNotFoundError
2. Create RequestComment entity
3. Save comment
4. Create RequestEvent (type=comment_added, data={comment_id, author_id})
5. Return comment

### AddNoteCommand + Handler

```python
@dataclass
class AddNoteCommand:
    request_id: str
    company_id: str
    author_id: str
    body: str
```

Handler: Same flow as AddComment but with RequestNote.

### ListCommentsQuery + Handler

```python
@dataclass
class ListCommentsQuery:
    request_id: str
    company_id: str
```

Handler:
1. Find request -> RequestNotFoundError
2. Return repo.find_comments(request_id)

### ListNotesQuery + Handler

Same pattern as ListComments.

---

## HTTP Layer

### New Schemas

```python
class AddCommentRequest(BaseModel):
    body: str = Field(min_length=1)

class CommentResponse(BaseModel):
    id: str
    request_id: str
    author_id: str
    body: str
    created_at: Optional[datetime] = None

class NoteResponse(BaseModel):
    id: str
    request_id: str
    author_id: str
    body: str
    created_at: Optional[datetime] = None
```

### New Endpoints

```python
@router.post("/{request_id}/comments", status_code=201)
def add_comment(request_id, body: AddCommentRequest, current_user, db):
    # Access control: employee can only comment on own requests
    # Technician+ can comment on any
    ...

@router.get("/{request_id}/comments")
def list_comments(request_id, current_user, db):
    # Same access control as add_comment
    ...

@router.post("/{request_id}/notes", status_code=201)
def add_note(request_id, body: AddCommentRequest, current_user, db):
    # require_role(TECHNICIAN)
    ...

@router.get("/{request_id}/notes")
def list_notes(request_id, current_user, db):
    # require_role(TECHNICIAN)
    ...
```

### Access Control Pattern

For comments:
- Check if current_user role >= TECHNICIAN -> allowed on any company request
- Otherwise check if request.created_by == current_user.id -> allowed on own
- Otherwise -> 404

For notes:
- require_role(TECHNICIAN) at router level -> only technicians

---

## Decisions

1. **Separate tables, separate endpoints**: Comments and notes never share endpoints. This eliminates any risk of leaking internal notes to employees.
2. **No edit/delete for v1**: Comments and notes are append-only, matching the event sourcing philosophy.
3. **Access control in router, not command handler**: The command handler trusts that authorization has been verified. The router performs the role/ownership check before calling the handler.
4. **Events for comments/notes**: Every comment/note creates a RequestEvent for audit trail. The event stores the comment/note ID for correlation.
