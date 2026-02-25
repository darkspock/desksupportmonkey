"""
Backfill default workflow templates for companies that don't have any.

Usage:
    PYTHONPATH=src python scripts/backfill_workflow_templates.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import SessionLocal
from src.company_bc.company.infrastructure.models import CompanyModel
from src.company_bc.company.application.commands.create_company import (
    DEFAULT_WORKFLOW_TEMPLATES,
)
from src.workflow_bc.template.domain.entities import (
    ChecklistItemDefinition,
    WorkflowTemplate,
)
from src.workflow_bc.template.infrastructure.repository import WorkflowTemplateRepository


def main():
    session = SessionLocal()
    try:
        repo = WorkflowTemplateRepository(session)
        companies = session.query(CompanyModel).filter_by(is_active=True).all()

        total = 0
        for company in companies:
            existing = repo.find_by_company(company.id)
            if existing:
                print(f"  SKIP {company.name} — already has {len(existing)} templates")
                continue

            for i, spec in enumerate(DEFAULT_WORKFLOW_TEMPLATES):
                template = WorkflowTemplate.create(
                    company_id=company.id,
                    name=spec["name"],
                    description=spec.get("description"),
                    require_all_complete=spec.get("require_all_complete", False),
                    sort_order=i,
                )
                items = []
                for j, item_spec in enumerate(spec.get("checklist_items", [])):
                    items.append(
                        ChecklistItemDefinition.create(
                            template_id=template.id,
                            title=item_spec["title"],
                            is_required=item_spec.get("is_required", True),
                            sort_order=j,
                        )
                    )
                template.set_checklist_items(items)
                repo.save(template)
                total += 1

            print(f"  OK   {company.name} — created {len(DEFAULT_WORKFLOW_TEMPLATES)} templates")

        session.commit()
        print(f"\nDone. Created {total} templates total.")
    finally:
        session.close()


if __name__ == "__main__":
    main()
