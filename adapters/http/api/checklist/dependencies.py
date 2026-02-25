from fastapi import Depends
from sqlalchemy.orm import Session

from core.database import get_db
from src.workflow_bc.checklist.infrastructure.repository import ChecklistItemRepository
from src.workflow_bc.template.infrastructure.repository import WorkflowTemplateRepository


def get_checklist_repo(
    db: Session = Depends(get_db),
) -> ChecklistItemRepository:
    return ChecklistItemRepository(db)


def get_template_repo_for_checklist(
    db: Session = Depends(get_db),
) -> WorkflowTemplateRepository:
    return WorkflowTemplateRepository(db)
