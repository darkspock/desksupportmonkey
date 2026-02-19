import logging
from dataclasses import dataclass
from typing import Optional

from src.company_bc.department.domain.repository import DepartmentRepositoryInterface
from src.framework.application.command_bus import Command, CommandHandler
from src.procurement_bc.purchase_order.domain.repository import (
    PurchaseOrderRepositoryInterface,
)

logger = logging.getLogger(__name__)


class DepartmentNotFoundError(Exception):
    pass


class DepartmentHasUsersError(Exception):
    pass


class DepartmentHasOpenPOsError(Exception):
    pass


@dataclass
class DeleteDepartmentCommand(Command):
    department_id: str
    company_id: str


class DeleteDepartmentCommandHandler(CommandHandler[DeleteDepartmentCommand]):
    def __init__(
        self,
        department_repo: DepartmentRepositoryInterface,
        po_repo: Optional[PurchaseOrderRepositoryInterface] = None,
    ):
        self.department_repo = department_repo
        self.po_repo = po_repo

    def handle(self, command: DeleteDepartmentCommand) -> None:
        department = self.department_repo.find_by_id(command.department_id, command.company_id)
        if not department:
            raise DepartmentNotFoundError("Department not found")

        user_count = self.department_repo.count_users(command.department_id)
        if user_count > 0:
            raise DepartmentHasUsersError(
                f"Cannot delete department with {user_count} assigned user(s)"
            )

        if self.po_repo:
            open_po_count = self.po_repo.count_by_department_non_terminal(
                command.company_id, command.department_id,
            )
            if open_po_count > 0:
                raise DepartmentHasOpenPOsError(
                    f"Cannot delete department with {open_po_count} open purchase order(s)"
                )

        department.deactivate()
        self.department_repo.save(department)
        logger.info("Department deactivated: %s", department.id)
