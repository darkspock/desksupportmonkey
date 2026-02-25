import pytest

from src.workflow_bc.checklist.domain.entities import RequestChecklistItem


class TestRequestChecklistItem:
    def test_create_success(self):
        item = RequestChecklistItem.create(
            request_id="01REQ",
            title="Wipe computer",
            description="Factory reset device",
            is_required=True,
        )
        assert item.title == "Wipe computer"
        assert item.is_completed is False
        assert item.completed_by is None
        assert item.is_required is True
        assert item.created_at is not None

    def test_create_empty_title_raises(self):
        with pytest.raises(ValueError, match="required"):
            RequestChecklistItem.create(request_id="01REQ", title="")

    def test_toggle_complete(self):
        item = RequestChecklistItem.create(request_id="01REQ", title="Task")
        item.toggle("user1")
        assert item.is_completed is True
        assert item.completed_by == "user1"
        assert item.completed_at is not None

    def test_toggle_uncomplete(self):
        item = RequestChecklistItem.create(request_id="01REQ", title="Task")
        item.toggle("user1")
        item.toggle("user2")
        assert item.is_completed is False
        assert item.completed_by is None
        assert item.completed_at is None

    def test_assign(self):
        item = RequestChecklistItem.create(request_id="01REQ", title="Task")
        item.assign("user1")
        assert item.assignee_id == "user1"

    def test_assign_none(self):
        item = RequestChecklistItem.create(
            request_id="01REQ", title="Task", assignee_id="user1"
        )
        item.assign(None)
        assert item.assignee_id is None
