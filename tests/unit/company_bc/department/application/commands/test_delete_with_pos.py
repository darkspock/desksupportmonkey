import pytest
from unittest.mock import MagicMock

from src.company_bc.department.application.commands.delete_department import (
    DeleteDepartmentCommand,
    DeleteDepartmentCommandHandler,
    DepartmentHasOpenPOsError,
)
from src.company_bc.department.domain.entities import Department


def _make_department() -> Department:
    return Department(
        id="dept1",
        company_id="comp1",
        name="Engineering",
        is_active=True,
    )


class TestDeleteDepartmentWithPOs:
    def setup_method(self):
        self.dept_repo = MagicMock()
        self.po_repo = MagicMock()

    def test_delete_blocked_by_open_pos(self):
        dept = _make_department()
        self.dept_repo.find_by_id.return_value = dept
        self.dept_repo.count_users.return_value = 0
        self.po_repo.count_by_department_non_terminal.return_value = 3

        handler = DeleteDepartmentCommandHandler(
            department_repo=self.dept_repo,
            po_repo=self.po_repo,
        )

        with pytest.raises(DepartmentHasOpenPOsError):
            handler.handle(
                DeleteDepartmentCommand(
                    department_id="dept1",
                    company_id="comp1",
                )
            )

    def test_delete_allowed_when_pos_are_terminal(self):
        dept = _make_department()
        self.dept_repo.find_by_id.return_value = dept
        self.dept_repo.count_users.return_value = 0
        self.po_repo.count_by_department_non_terminal.return_value = 0

        handler = DeleteDepartmentCommandHandler(
            department_repo=self.dept_repo,
            po_repo=self.po_repo,
        )

        handler.handle(
            DeleteDepartmentCommand(
                department_id="dept1",
                company_id="comp1",
            )
        )

        self.dept_repo.save.assert_called_once()
