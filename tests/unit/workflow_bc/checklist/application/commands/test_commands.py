from unittest.mock import MagicMock

import pytest

from src.workflow_bc.checklist.application.commands.generate_checklist import (
    GenerateChecklistCommand,
    GenerateChecklistCommandHandler,
)
from src.workflow_bc.checklist.application.commands.toggle_item import (
    ToggleChecklistItemCommand,
    ToggleChecklistItemCommandHandler,
)
from src.workflow_bc.checklist.application.commands.assign_item import (
    AssignChecklistItemCommand,
    AssignChecklistItemCommandHandler,
)
from src.workflow_bc.checklist.application.commands.add_item import (
    AddChecklistItemCommand,
    AddChecklistItemCommandHandler,
)
from src.workflow_bc.checklist.application.commands.remove_item import (
    RemoveChecklistItemCommand,
    RemoveChecklistItemCommandHandler,
)
from src.workflow_bc.checklist.domain.entities import RequestChecklistItem
from src.workflow_bc.checklist.domain.exceptions import ChecklistItemNotFoundError
from src.workflow_bc.template.domain.entities import (
    ChecklistItemDefinition,
    WorkflowTemplate,
)


class TestGenerateChecklistCommandHandler:
    def test_generate_from_template(self):
        template = WorkflowTemplate.create(
            company_id="01COMP", name="Offboarding", require_all_complete=True
        )
        template.set_checklist_items([
            ChecklistItemDefinition.create(
                template_id=template.id, title="Disable email", sort_order=0
            ),
            ChecklistItemDefinition.create(
                template_id=template.id, title="Collect badge", sort_order=1
            ),
        ])

        template_repo = MagicMock()
        template_repo.find_by_id.return_value = template
        checklist_repo = MagicMock()

        handler = GenerateChecklistCommandHandler(
            template_repo=template_repo, checklist_repo=checklist_repo
        )
        handler.handle(
            GenerateChecklistCommand(
                request_id="01REQ",
                template_id=template.id,
                company_id="01COMP",
            )
        )

        checklist_repo.save_all.assert_called_once()
        items = checklist_repo.save_all.call_args[0][0]
        assert len(items) == 2
        assert items[0].title == "Disable email"
        assert items[0].require_all_complete is True
        assert items[1].title == "Collect badge"

    def test_generate_no_template(self):
        template_repo = MagicMock()
        template_repo.find_by_id.return_value = None
        checklist_repo = MagicMock()

        handler = GenerateChecklistCommandHandler(
            template_repo=template_repo, checklist_repo=checklist_repo
        )
        handler.handle(
            GenerateChecklistCommand(
                request_id="01REQ",
                template_id="01MISSING",
                company_id="01COMP",
            )
        )

        checklist_repo.save_all.assert_not_called()


class TestToggleChecklistItemCommandHandler:
    def test_toggle_success(self):
        repo = MagicMock()
        item = RequestChecklistItem.create(request_id="01REQ", title="Task")
        repo.find_by_id.return_value = item

        handler = ToggleChecklistItemCommandHandler(repo=repo)
        handler.handle(ToggleChecklistItemCommand(item_id=item.id, user_id="user1"))

        repo.save.assert_called_once()
        saved = repo.save.call_args[0][0]
        assert saved.is_completed is True
        assert saved.completed_by == "user1"

    def test_toggle_not_found(self):
        repo = MagicMock()
        repo.find_by_id.return_value = None

        handler = ToggleChecklistItemCommandHandler(repo=repo)
        with pytest.raises(ChecklistItemNotFoundError):
            handler.handle(
                ToggleChecklistItemCommand(item_id="01MISSING", user_id="user1")
            )


class TestAssignChecklistItemCommandHandler:
    def test_assign_success(self):
        repo = MagicMock()
        item = RequestChecklistItem.create(request_id="01REQ", title="Task")
        repo.find_by_id.return_value = item

        handler = AssignChecklistItemCommandHandler(repo=repo)
        handler.handle(
            AssignChecklistItemCommand(item_id=item.id, assignee_id="user2")
        )

        repo.save.assert_called_once()
        saved = repo.save.call_args[0][0]
        assert saved.assignee_id == "user2"

    def test_assign_not_found(self):
        repo = MagicMock()
        repo.find_by_id.return_value = None

        handler = AssignChecklistItemCommandHandler(repo=repo)
        with pytest.raises(ChecklistItemNotFoundError):
            handler.handle(
                AssignChecklistItemCommand(item_id="01MISSING", assignee_id="user2")
            )


class TestAddChecklistItemCommandHandler:
    def test_add_success(self):
        repo = MagicMock()
        repo.find_by_request.return_value = []

        handler = AddChecklistItemCommandHandler(repo=repo)
        handler.handle(
            AddChecklistItemCommand(
                request_id="01REQ",
                title="New task",
                description="Ad-hoc item",
            )
        )

        repo.save.assert_called_once()
        saved = repo.save.call_args[0][0]
        assert saved.title == "New task"
        assert saved.sort_order == 0

    def test_add_increments_sort_order(self):
        repo = MagicMock()
        existing = RequestChecklistItem.create(
            request_id="01REQ", title="Existing", sort_order=2
        )
        repo.find_by_request.return_value = [existing]

        handler = AddChecklistItemCommandHandler(repo=repo)
        handler.handle(
            AddChecklistItemCommand(request_id="01REQ", title="New")
        )

        saved = repo.save.call_args[0][0]
        assert saved.sort_order == 3


class TestRemoveChecklistItemCommandHandler:
    def test_remove_success(self):
        repo = MagicMock()
        item = RequestChecklistItem.create(request_id="01REQ", title="Task")
        repo.find_by_id.return_value = item

        handler = RemoveChecklistItemCommandHandler(repo=repo)
        handler.handle(RemoveChecklistItemCommand(item_id=item.id))

        repo.delete.assert_called_once_with(item.id)

    def test_remove_not_found(self):
        repo = MagicMock()
        repo.find_by_id.return_value = None

        handler = RemoveChecklistItemCommandHandler(repo=repo)
        with pytest.raises(ChecklistItemNotFoundError):
            handler.handle(RemoveChecklistItemCommand(item_id="01MISSING"))
