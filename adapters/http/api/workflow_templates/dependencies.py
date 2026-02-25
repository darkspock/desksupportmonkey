from fastapi import Depends
from sqlalchemy.orm import Session

from core.database import get_db
from src.workflow_bc.template.infrastructure.repository import WorkflowTemplateRepository


def get_workflow_template_repo(
    db: Session = Depends(get_db),
) -> WorkflowTemplateRepository:
    return WorkflowTemplateRepository(db)
