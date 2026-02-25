"""
Backfill service_requests with workflow_template_id and workflow_subtype_id.

Matches existing request.type values to workflow_templates.name for each company.
Idempotent: only updates rows where workflow_template_id IS NULL.

Usage:
    PYTHONPATH=src python scripts/backfill_request_templates.py
"""

import os
import sys

sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)

from core.database import SessionLocal  # noqa: E402
from src.request_bc.request.infrastructure.models import (  # noqa: E402
    ServiceRequestModel,
)
from src.workflow_bc.template.infrastructure.models import (  # noqa: E402
    WorkflowTemplateModel,
    WorkflowSubtypeModel,
)
from src.company_bc.company.infrastructure.models import (  # noqa: E402
    CompanyModel,
)


def _normalize(name: str) -> str:
    """Convert template name to request type value.

    'New Equipment' -> 'new_equipment'
    'Access Request' -> 'access_request'
    """
    return name.lower().replace(" ", "_")


def main():
    print("=" * 60)
    print("Backfill: Link service_requests to workflow_templates")
    print("=" * 60)
    print()

    session = SessionLocal()
    total_matched = 0
    total_unmatched = 0
    total_subtype_matched = 0

    try:
        companies = session.query(CompanyModel).all()
        print(f"Found {len(companies)} companies\n")

        for company in companies:
            cid = company.id
            print(f"Company: {company.name} ({cid})")

            # Build template name map
            templates = (
                session.query(WorkflowTemplateModel)
                .filter_by(company_id=cid)
                .all()
            )
            # normalized_type -> template
            tmpl_map: dict[str, WorkflowTemplateModel] = {}
            for t in templates:
                tmpl_map[_normalize(t.name)] = t

            # Build subtype map: (template_id, normalized_name) -> id
            subtype_map: dict[tuple[str, str], str] = {}
            for t in templates:
                subtypes = (
                    session.query(WorkflowSubtypeModel)
                    .filter_by(template_id=t.id)
                    .all()
                )
                for s in subtypes:
                    subtype_map[(t.id, s.name.lower())] = s.id

            # Find unlinked requests
            requests = (
                session.query(ServiceRequestModel)
                .filter_by(company_id=cid)
                .filter(
                    ServiceRequestModel.workflow_template_id.is_(None)
                )
                .all()
            )

            matched = 0
            unmatched = 0
            sub_matched = 0

            for req in requests:
                tmpl = tmpl_map.get(req.type)
                if tmpl:
                    req.workflow_template_id = tmpl.id
                    matched += 1

                    if req.subtype:
                        sid = subtype_map.get(
                            (tmpl.id, req.subtype.lower())
                        )
                        if sid:
                            req.workflow_subtype_id = sid
                            sub_matched += 1
                else:
                    unmatched += 1

            session.commit()

            total_matched += matched
            total_unmatched += unmatched
            total_subtype_matched += sub_matched

            print(
                f"  Requests: {len(requests)} unlinked, "
                f"{matched} matched, {unmatched} unmatched, "
                f"{sub_matched} subtypes linked"
            )

        print()
        print("-" * 60)
        print(f"Total: {total_matched} matched, "
              f"{total_unmatched} unmatched, "
              f"{total_subtype_matched} subtypes linked")
        print("Done.")

    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    main()
