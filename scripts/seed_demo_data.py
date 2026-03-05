"""
Seed script for DeskSupportMonkey demo data.

Creates realistic demo data across all tables:
- 3 companies with email domains
- 1 super admin + users per role per company
- Departments, assets, service requests, comments, notes, events, notifications, reports

Usage:
    PYTHONPATH=src python scripts/seed_demo_data.py

Idempotent: clears all existing data before seeding.

The ``seed_company_data`` function can also be imported and used to populate
demo data for a single company (e.g. reseller demo accounts).
"""

import os
import sys
import random
from typing import Any
from datetime import datetime, date, timedelta

import ulid

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import SessionLocal, engine
from core.base import Base

# Models
from src.company_bc.company.infrastructure.models import CompanyModel, CompanyEmailDomainModel
from src.company_bc.department.infrastructure.models import DepartmentModel
from src.auth_bc.user.infrastructure.models import UserModel
from src.asset_bc.asset.infrastructure.models import AssetModel, AssetEventModel, AssetLocationModel
from src.request_bc.request.infrastructure.models import (
    ServiceRequestModel, RequestEventModel, RequestCommentModel, RequestNoteModel,
)
from src.notification_bc.notification.infrastructure.models import NotificationModel
from src.report_bc.report.infrastructure.models import ReportModel
from src.company_bc.employee_role.infrastructure.models import EmployeeRoleModel  # noqa: F401 — needed for FK resolution

# Custom field definitions
from src.custom_field_bc.definition.domain.entities import CustomFieldDefinition
from src.custom_field_bc.definition.infrastructure.repository import CustomFieldDefinitionRepository
from src.custom_field_bc.definition.infrastructure.models import CustomFieldDefinitionModel

# Asset type definitions
from src.asset_type_bc.definition.infrastructure.models import AssetTypeDefinitionModel

# Workflow templates
from src.workflow_bc.template.domain.entities import (
    WorkflowTemplate,
    ChecklistItemDefinition,
    WorkflowSubtype,
)
from src.workflow_bc.template.infrastructure.models import WorkflowTemplateModel
from src.workflow_bc.template.infrastructure.repository import WorkflowTemplateRepository


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def uid() -> str:
    return str(ulid.new())


def past_date(days_ago: int) -> datetime:
    return datetime.utcnow() - timedelta(days=days_ago)


def past_date_only(days_ago: int) -> date:
    return date.today() - timedelta(days=days_ago)


random.seed(42)  # reproducible

# ---------------------------------------------------------------------------
# Data definitions
# ---------------------------------------------------------------------------

COMPANIES = [
    {"name": "TechCorp Inc", "domains": ["techcorp.com"]},
    {"name": "FinanceHub", "domains": ["financehub.com", "finhub.io"]},
    {"name": "HealthCare Plus", "domains": ["healthcareplus.com"]},
]

DEPARTMENTS = ["Engineering", "Sales", "HR", "IT"]

FIRST_NAMES = [
    "Alice", "Bob", "Carol", "Dave", "Eve", "Frank", "Grace", "Hank",
    "Iris", "Jack", "Karen", "Leo", "Mona", "Nick", "Olivia", "Paul",
    "Quinn", "Rita", "Sam", "Tina", "Uma", "Vince", "Wendy", "Xander",
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller",
    "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez",
    "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin",
]

ASSET_CATALOG = [
    # (type, brand, model, base_serial_prefix)
    ("laptop", "Dell", "Latitude 5540", "DL55"),
    ("laptop", "Apple", "MacBook Pro 14", "AMBP"),
    ("laptop", "Lenovo", "ThinkPad T14", "LTP14"),
    ("monitor", "Dell", "UltraSharp U2723QE", "DU27"),
    ("monitor", "LG", "27UK850-W", "LG27"),
    ("keyboard", "Logitech", "MX Keys", "LGMX"),
    ("keyboard", "Apple", "Magic Keyboard", "AMGK"),
    ("mouse", "Logitech", "MX Master 3S", "LGM3"),
    ("mouse", "Apple", "Magic Mouse", "AMGM"),
    ("headset", "Jabra", "Evolve2 75", "JBE2"),
    ("headset", "Sony", "WH-1000XM5", "SNWH"),
    ("docking_station", "CalDigit", "TS4", "CDTS"),
    ("docking_station", "Anker", "PowerExpand", "AKPE"),
]

REQUEST_TEMPLATES = [
    # (type, title, description, priority)
    ("incident", "Laptop not booting", "My laptop shows a blue screen on startup and won't proceed past the loading screen.", "high"),
    ("incident", "Monitor flickering", "My external monitor keeps flickering every few seconds, making it impossible to work.", "medium"),
    ("incident", "VPN connection drops", "The VPN disconnects every 10-15 minutes, disrupting my remote work.", "high"),
    ("incident", "Keyboard keys stuck", "Several keys on my keyboard are stuck and not registering properly.", "low"),
    ("incident", "Slow computer performance", "My computer has become extremely slow, applications take minutes to open.", "medium"),
    ("new_equipment", "Request new laptop", "I need a new laptop for my upcoming project. Current one is 4 years old.", "low"),
    ("new_equipment", "Additional monitor", "Requesting a second monitor for improved productivity with dual-screen setup.", "low"),
    ("new_equipment", "Docking station needed", "Need a docking station to connect my laptop to peripherals at my desk.", "low"),
    ("onboarding", "New hire setup - Engineering", "New engineer starting next Monday. Needs laptop, monitor, keyboard, mouse, and headset.", "medium"),
    ("onboarding", "New hire setup - Sales", "New sales rep joining the team. Needs laptop and basic peripherals.", "medium"),
    ("onboarding", "New hire setup - HR", "New HR coordinator starting. Standard equipment package needed.", "medium"),
    ("incident", "Email sync issues", "Outlook is not syncing new emails. Tried restarting but the problem persists.", "urgent"),
]

COMMENT_TEMPLATES = [
    "I've tried restarting but the issue persists.",
    "This has been happening since yesterday.",
    "Is there an ETA for this?",
    "Thanks for looking into this quickly!",
    "The issue seems to be getting worse.",
    "I can provide more details if needed.",
]

NOTE_TEMPLATES = [
    "Checked hardware diagnostics — no issues found. Likely software related.",
    "Ordered replacement part. Expected delivery in 2 business days.",
    "Escalated to vendor support. Waiting for callback.",
    "Resolved by reinstalling drivers. Monitoring for recurrence.",
    "User confirmed issue is intermittent. Scheduled follow-up check.",
    "Checked inventory — have spare units available.",
]

SYSTEM_LOCATIONS = [
    ("employee", "Empleado"),
    ("in_transit", "En Tránsito"),
    ("main_warehouse", "Almacén Principal"),
]

CUSTOM_LOCATIONS = [
    {
        "name": "Sala de Servidores",
        "street_line_1": "100 Tech Park Dr",
        "city": "Austin",
        "state": "TX",
        "postal_code": "78701",
        "country": "US",
    },
    {
        "name": "Recepción",
        "street_line_1": "200 Corporate Blvd",
        "city": "Austin",
        "state": "TX",
        "postal_code": "78702",
        "country": "US",
    },
    {
        "name": "Sala de Reuniones A",
        "street_line_1": "200 Corporate Blvd",
        "street_line_2": "Floor 3",
        "city": "Austin",
        "state": "TX",
        "postal_code": "78702",
        "country": "US",
    },
]

DEFAULT_ASSET_TYPES = [
    ("laptop", "Laptop", "laptop", 0),
    ("monitor", "Monitor", "monitor", 1),
    ("keyboard", "Keyboard", "keyboard", 2),
    ("mouse", "Mouse", "mouse", 3),
    ("headset", "Headset", "headset", 4),
    ("phone", "Phone", "phone", 5),
    ("docking_station", "Docking Station", "dock", 6),
    ("other", "Other", None, 7),
]

# Custom field specs
CUSTOM_FIELD_SPECS: dict[str, list[dict[str, Any]]] = {
    "asset": [
        {"label": "Cost Center", "field_type": "text", "required": True, "sort_order": 0},
        {"label": "Insurance Policy", "field_type": "text", "required": False, "sort_order": 1},
        {"label": "Building", "field_type": "select", "options": ["HQ", "Branch A", "Branch B", "Remote"], "sort_order": 2},
        {"label": "Is Leased", "field_type": "boolean", "sort_order": 3},
        {"label": "Floor", "field_type": "number", "sort_order": 4},
    ],
    "request": [
        {"label": "Budget Code", "field_type": "text", "sort_order": 0},
        {"label": "Urgency Reason", "field_type": "select", "options": ["Business Critical", "Standard", "Low Priority"], "sort_order": 1},
    ],
    "incident": [
        {"label": "Affected Systems", "field_type": "multi_select", "options": ["Email", "VPN", "CRM", "ERP", "Network"], "sort_order": 0},
        {"label": "External Vendor", "field_type": "text", "sort_order": 1},
    ],
}

ASSET_CUSTOM_FIELD_SAMPLES: list[dict[str, Any]] = [
    {"cost_center": "IT-001", "insurance_policy": "POL-2024-A1", "building": "HQ", "is_leased": False, "floor": 3},
    {"cost_center": "IT-002", "building": "Branch A", "is_leased": True, "floor": 1},
    {"cost_center": "ENG-010", "building": "Remote", "is_leased": False},
]

REQUEST_CUSTOM_FIELD_SAMPLES: list[dict[str, Any]] = [
    {"budget_code": "BUD-2025-Q1", "urgency_reason": "Business Critical"},
    {"budget_code": "BUD-2025-Q2", "urgency_reason": "Standard"},
    {"budget_code": "BUD-2025-Q3", "urgency_reason": "Low Priority"},
]

WORKFLOW_TEMPLATE_SPECS: list[dict[str, Any]] = [
    {
        "name": "Incident",
        "description": "Report a technical issue or outage",
        "icon": "circle-alert",
        "require_all_complete": False,
        "subtypes": [],
        "checklist_items": [
            {"title": "Identify root cause", "is_required": True},
            {"title": "Apply fix or workaround", "is_required": True},
            {"title": "Verify resolution with reporter", "is_required": True},
            {"title": "Update documentation", "is_required": False},
        ],
    },
    {
        "name": "New Equipment",
        "description": "Request new hardware or software",
        "icon": "monitor",
        "require_all_complete": True,
        "subtypes": [
            {"name": "Computer"},
            {"name": "Mobile"},
            {"name": "Peripheral"},
            {"name": "Monitor"},
            {"name": "Software License"},
        ],
        "checklist_items": [
            {"title": "Verify budget approval", "is_required": True},
            {"title": "Place purchase order", "is_required": True},
            {"title": "Receive and inspect equipment", "is_required": True},
            {"title": "Configure and install", "is_required": True},
            {"title": "Deliver to employee", "is_required": True},
            {"title": "Confirm employee acceptance", "is_required": True},
        ],
    },
    {
        "name": "Onboarding",
        "description": "Set up accounts, equipment, and access for new hire",
        "icon": "user-plus",
        "require_all_complete": True,
        "subtypes": [],
        "checklist_items": [
            {"title": "Create user accounts (email, Slack, etc.)", "is_required": True},
            {"title": "Assign laptop and peripherals", "is_required": True},
            {"title": "Set up VPN and network access", "is_required": True},
            {"title": "Grant application permissions", "is_required": True},
            {"title": "Ship equipment to employee", "is_required": True},
            {"title": "Schedule orientation call", "is_required": False},
            {"title": "Add to team channels", "is_required": False},
        ],
    },
    {
        "name": "Repair",
        "description": "Fix or restore malfunctioning hardware or software",
        "icon": "wrench",
        "require_all_complete": True,
        "subtypes": [
            {"name": "Hardware"},
            {"name": "Software"},
            {"name": "Network"},
            {"name": "Security"},
            {"name": "Other"},
        ],
        "checklist_items": [
            {"title": "Diagnose the issue", "is_required": True},
            {"title": "Order replacement parts (if needed)", "is_required": False},
            {"title": "Apply repair or workaround", "is_required": True},
            {"title": "Test and verify fix", "is_required": True},
            {"title": "Return equipment to user", "is_required": True},
        ],
    },
    {
        "name": "Configuration",
        "description": "Software installation, account setup, or permissions change",
        "icon": "settings",
        "require_all_complete": True,
        "subtypes": [
            {"name": "Software Install"},
            {"name": "Account Setup"},
            {"name": "Permissions"},
        ],
        "checklist_items": [
            {"title": "Review request details", "is_required": True},
            {"title": "Apply configuration change", "is_required": True},
            {"title": "Verify with requester", "is_required": True},
        ],
    },
    {
        "name": "Access Request",
        "description": "Request access to systems, applications, or physical spaces",
        "icon": "lock",
        "require_all_complete": True,
        "subtypes": [
            {"name": "System Access"},
            {"name": "Physical Access"},
            {"name": "VPN"},
        ],
        "checklist_items": [
            {"title": "Verify manager approval", "is_required": True},
            {"title": "Provision access", "is_required": True},
            {"title": "Confirm access works", "is_required": True},
        ],
    },
]


# ---------------------------------------------------------------------------
# Per-company seed functions
# ---------------------------------------------------------------------------

def seed_departments_for_company(session, company_id: str) -> list[dict]:
    """Create departments for a single company (idempotent). Returns [{id, name}]."""
    existing = {
        row[0]: row[1]
        for row in session.query(DepartmentModel.name, DepartmentModel.id).filter_by(
            company_id=company_id,
        ).all()
    }
    depts = []
    for name in DEPARTMENTS:
        if name in existing:
            depts.append({"id": existing[name], "name": name})
            continue
        dept = DepartmentModel(
            id=uid(), company_id=company_id, name=name, is_active=True,
        )
        session.add(dept)
        session.flush()
        depts.append({"id": dept.id, "name": name})
    return depts


def seed_locations_for_company(session, company_id: str) -> dict:
    """Create asset locations for a single company. Returns {key: location_id}."""
    locs: dict[str, str] = {}
    for system_key, name in SYSTEM_LOCATIONS:
        existing = session.query(AssetLocationModel).filter_by(
            company_id=company_id, system_key=system_key,
        ).first()
        if existing:
            locs[system_key] = existing.id
        else:
            loc = AssetLocationModel(
                id=uid(), company_id=company_id, name=name,
                is_system=True, system_key=system_key, in_use=True,
            )
            session.add(loc)
            session.flush()
            locs[system_key] = loc.id
    for loc_spec in CUSTOM_LOCATIONS:
        loc = AssetLocationModel(
            id=uid(), company_id=company_id, name=loc_spec["name"],
            is_system=False, in_use=True,
            street_line_1=loc_spec.get("street_line_1"),
            street_line_2=loc_spec.get("street_line_2"),
            city=loc_spec.get("city"),
            state=loc_spec.get("state"),
            postal_code=loc_spec.get("postal_code"),
            country=loc_spec.get("country"),
        )
        session.add(loc)
        session.flush()
        locs[loc_spec["name"]] = loc.id
    return locs


def seed_users_for_company(session, company_id: str, domain: str, dept_map: list[dict]) -> dict:
    """Create users for a single company.

    Returns {role: [user_dicts]} where each user_dict has {id, email, name}.
    """
    name_idx = 0

    def next_name():
        nonlocal name_idx
        first = FIRST_NAMES[name_idx % len(FIRST_NAMES)]
        last = LAST_NAMES[name_idx % len(LAST_NAMES)]
        name_idx += 1
        return first, last

    users: dict[str, list] = {
        "admin": [], "procurement_manager": [], "technician": [], "employee": [],
    }

    # Admin
    first, last = next_name()
    admin = UserModel(
        id=uid(),
        email=f"{first.lower()}.{last.lower()}@{domain}",
        name=f"{first} {last}",
        role="admin",
        company_id=company_id,
        department_id=dept_map[0]["id"],
        is_active=True,
    )
    session.add(admin)
    users["admin"].append({"id": admin.id, "email": admin.email, "name": admin.name})

    # Procurement Manager
    first, last = next_name()
    pm = UserModel(
        id=uid(),
        email=f"{first.lower()}.{last.lower()}@{domain}",
        name=f"{first} {last}",
        role="procurement_manager",
        company_id=company_id,
        department_id=dept_map[0]["id"],
        is_active=True,
    )
    session.add(pm)
    users["procurement_manager"].append({"id": pm.id, "email": pm.email, "name": pm.name})

    # Technicians (2)
    for _ in range(2):
        first, last = next_name()
        tech = UserModel(
            id=uid(),
            email=f"{first.lower()}.{last.lower()}@{domain}",
            name=f"{first} {last}",
            role="technician",
            company_id=company_id,
            department_id=dept_map[3]["id"],  # IT
            is_active=True,
        )
        session.add(tech)
        users["technician"].append({"id": tech.id, "email": tech.email, "name": tech.name})

    # Employees (5)
    for j in range(5):
        first, last = next_name()
        dept = dept_map[j % len(dept_map)]
        emp = UserModel(
            id=uid(),
            email=f"{first.lower()}.{last.lower()}@{domain}",
            name=f"{first} {last}",
            role="employee",
            company_id=company_id,
            department_id=dept["id"],
            is_active=True,
        )
        session.add(emp)
        users["employee"].append({"id": emp.id, "email": emp.email, "name": emp.name})

    return users


def seed_asset_type_definitions_for_company(session, company_id: str) -> None:
    """Create default asset type definitions for a single company (idempotent)."""
    existing_codes = {
        row[0]
        for row in session.query(AssetTypeDefinitionModel.code).filter_by(
            company_id=company_id,
        ).all()
    }
    now = datetime.utcnow()
    for code, name, icon, sort_order in DEFAULT_ASSET_TYPES:
        if code in existing_codes:
            continue
        session.add(AssetTypeDefinitionModel(
            id=uid(),
            company_id=company_id,
            code=code,
            name=name,
            icon=icon,
            is_active=True,
            sort_order=sort_order,
            created_at=now,
            updated_at=now,
        ))


def seed_assets_for_company(
    session, company_id: str, users: dict, dept_map: list[dict], loc_map: dict,
) -> list[str]:
    """Create assets for a single company. Returns list of asset IDs."""
    serial_counter = 1000
    employees = users["employee"]
    technicians = users["technician"]
    all_assignable = employees + technicians
    custom_loc_ids = [v for k, v in loc_map.items() if k not in ("employee", "in_transit", "main_warehouse")]
    asset_ids = []

    catalog_items = random.choices(ASSET_CATALOG, k=18)

    for i, (atype, brand, model, serial_prefix) in enumerate(catalog_items):
        serial_counter += 1
        serial = f"{serial_prefix}-{serial_counter:06d}"

        rand = random.random()
        if rand < 0.55:
            status = "assigned"
            assigned_to = all_assignable[i % len(all_assignable)]["id"]
            location_id = loc_map["employee"]
        elif rand < 0.80:
            status = "in_stock"
            assigned_to = None
            if random.random() < 0.7:
                location_id = loc_map["main_warehouse"]
            else:
                location_id = random.choice(custom_loc_ids)
        elif rand < 0.93:
            status = "in_repair"
            assigned_to = None
            location_id = loc_map["main_warehouse"]
        else:
            status = "decommissioned"
            assigned_to = None
            location_id = None

        days_ago = random.randint(30, 365)
        purchase = past_date_only(days_ago)
        if i < 3:
            warranty = date.today() + timedelta(days=random.randint(5, 25))
        elif i < 6:
            warranty = date.today() + timedelta(days=random.randint(60, 365))
        else:
            warranty = purchase + timedelta(days=random.randint(365, 1095))

        asset = AssetModel(
            id=uid(),
            company_id=company_id,
            type=atype,
            brand=brand,
            model=model,
            serial_number=serial,
            status=status,
            assigned_to=assigned_to,
            department_id=dept_map[i % len(dept_map)]["id"],
            location_id=location_id,
            purchase_date=purchase,
            warranty_expiration=warranty,
            notes=f"Demo asset #{i+1}" if i < 3 else None,
        )
        session.add(asset)
        session.flush()
        asset_ids.append(asset.id)

        admin_id = users["admin"][0]["id"]
        session.add(AssetEventModel(
            id=uid(),
            asset_id=asset.id,
            event_type="asset.created",
            data={"type": atype, "brand": brand, "model": model},
            performed_by=admin_id,
        ))
        if status == "assigned":
            session.add(AssetEventModel(
                id=uid(),
                asset_id=asset.id,
                event_type="asset.assigned",
                data={"assigned_to": assigned_to},
                performed_by=admin_id,
            ))

    return asset_ids


def seed_requests_for_company(session, company_id: str, users: dict) -> list[str]:
    """Create service requests for a single company. Returns list of request IDs."""
    employees = users["employee"]
    technicians = users["technician"]
    request_ids = []
    statuses_cycle = [
        "submitted", "in_review", "in_progress", "resolved", "resolved", "rejected",
        "submitted", "in_progress", "resolved", "in_review", "in_progress", "resolved",
    ]

    templates = list(REQUEST_TEMPLATES)
    random.shuffle(templates)

    for i, (rtype, title, desc, priority) in enumerate(templates):
        status = statuses_cycle[i % len(statuses_cycle)]
        created_by = employees[i % len(employees)]["id"]
        days_ago = random.randint(1, 80)

        assigned_to = None
        resolved_at = None
        if status in ("in_review", "in_progress", "resolved", "rejected"):
            assigned_to = technicians[i % len(technicians)]["id"]
        if status == "resolved":
            resolved_at = past_date(max(days_ago - random.randint(1, 10), 0))

        request = ServiceRequestModel(
            id=uid(),
            company_id=company_id,
            created_by=created_by,
            assigned_to=assigned_to,
            type=rtype,
            title=title,
            description=desc,
            status=status,
            priority=priority,
            data=None,
            resolved_at=resolved_at,
        )
        session.add(request)
        session.flush()
        request_ids.append(request.id)

        session.add(RequestEventModel(
            id=uid(),
            request_id=request.id,
            event_type="request.created",
            data={"type": rtype, "title": title, "priority": priority},
            performed_by=created_by,
        ))

        if status != "submitted":
            session.add(RequestEventModel(
                id=uid(),
                request_id=request.id,
                event_type="request.status_changed",
                data={"from": "submitted", "to": "in_review"},
                performed_by=assigned_to or technicians[0]["id"],
            ))
        if status in ("in_progress", "resolved"):
            session.add(RequestEventModel(
                id=uid(),
                request_id=request.id,
                event_type="request.status_changed",
                data={"from": "in_review", "to": "in_progress"},
                performed_by=assigned_to or technicians[0]["id"],
            ))
        if status == "resolved":
            session.add(RequestEventModel(
                id=uid(),
                request_id=request.id,
                event_type="request.status_changed",
                data={"from": "in_progress", "to": "resolved"},
                performed_by=assigned_to or technicians[0]["id"],
            ))
        if status == "rejected":
            session.add(RequestEventModel(
                id=uid(),
                request_id=request.id,
                event_type="request.status_changed",
                data={"from": "in_review", "to": "rejected"},
                performed_by=assigned_to or technicians[0]["id"],
            ))

        if random.random() < 0.6:
            comment_text = random.choice(COMMENT_TEMPLATES)
            session.add(RequestCommentModel(
                id=uid(),
                request_id=request.id,
                author_id=created_by,
                body=comment_text,
            ))
            if assigned_to and random.random() < 0.5:
                session.add(RequestCommentModel(
                    id=uid(),
                    request_id=request.id,
                    author_id=assigned_to,
                    body="We're looking into this. I'll update you shortly.",
                ))

        if assigned_to and random.random() < 0.4:
            note_text = random.choice(NOTE_TEMPLATES)
            session.add(RequestNoteModel(
                id=uid(),
                request_id=request.id,
                author_id=assigned_to,
                body=note_text,
            ))

    return request_ids


def seed_notifications_for_company(session, company_id: str, users: dict) -> int:
    """Create notifications for all users in a single company. Returns count."""
    event_types = [
        "request.created", "request.status_changed", "request.assigned",
        "request.comment_added", "report.ready",
    ]
    notification_templates = [
        ("New request submitted", "A new service request has been submitted."),
        ("Request status updated", "Your request status has been changed to in_progress."),
        ("Request assigned", "A request has been assigned to you."),
        ("New comment on request", "Someone commented on your service request."),
        ("Report ready", "Your requested report is ready for download."),
    ]

    total = 0
    all_users = (
        users["admin"] + users["procurement_manager"]
        + users["technician"] + users["employee"]
    )
    for user in all_users:
        count = random.randint(2, 5)
        for j in range(count):
            idx = j % len(notification_templates)
            title, body = notification_templates[idx]
            event_type = event_types[idx]
            is_read = random.random() < 0.4

            session.add(NotificationModel(
                id=uid(),
                user_id=user["id"],
                company_id=company_id,
                event_type=event_type,
                title=title,
                body=body,
                data={"demo": True},
                is_read=is_read,
            ))
            total += 1
    return total


def seed_reports_for_company(session, company_id: str, users: dict) -> int:
    """Create report records for a single company. Returns count."""
    report_types = ["asset_inventory", "request_summary", "technician_performance"]
    statuses = ["completed", "pending", "failed"]
    total = 0
    admin_id = users["admin"][0]["id"]

    for i, rtype in enumerate(report_types):
        status = statuses[i]
        report = ReportModel(
            id=uid(),
            company_id=company_id,
            requested_by=admin_id,
            type=rtype,
            status=status,
            parameters={"demo": True},
            storage_key=f"reports/{company_id}/{rtype}.pdf" if status == "completed" else None,
            error_message="Simulated failure for demo" if status == "failed" else None,
            completed_at=past_date(5) if status == "completed" else None,
        )
        session.add(report)
        total += 1
    return total


def seed_custom_field_definitions_for_company(session, company_id: str) -> None:
    """Create custom field definitions for a single company."""
    cf_repo = CustomFieldDefinitionRepository(session)
    for entity_type, specs in CUSTOM_FIELD_SPECS.items():
        for spec in specs:
            defn = CustomFieldDefinition.create(
                company_id=company_id,
                entity_type=entity_type,
                label=spec["label"],
                field_type=spec["field_type"],
                required=spec.get("required", False),
                options=spec.get("options"),
                sort_order=spec.get("sort_order", 0),
            )
            cf_repo.save(defn)


def seed_custom_field_values_for_company(
    session, asset_ids: list[str], request_ids: list[str],
) -> None:
    """Assign sample custom field values to some demo assets and requests."""
    for i, sample in enumerate(ASSET_CUSTOM_FIELD_SAMPLES):
        if i >= len(asset_ids):
            break
        asset = session.query(AssetModel).filter_by(id=asset_ids[i]).one()
        asset.custom_fields_data = sample

    for i, sample in enumerate(REQUEST_CUSTOM_FIELD_SAMPLES):
        if i >= len(request_ids):
            break
        request = session.query(ServiceRequestModel).filter_by(id=request_ids[i]).one()
        request.custom_fields_data = sample


def seed_workflow_templates_for_company(session, company_id: str) -> None:
    """Create workflow templates for a single company (idempotent)."""
    existing_names = {
        row[0]
        for row in session.query(WorkflowTemplateModel.name).filter_by(
            company_id=company_id,
        ).all()
    }
    repo = WorkflowTemplateRepository(session)
    for spec in WORKFLOW_TEMPLATE_SPECS:
        if spec["name"] in existing_names:
            continue
        template = WorkflowTemplate.create(
            company_id=company_id,
            name=spec["name"],
            description=spec.get("description"),
            icon=spec.get("icon"),
            require_all_complete=spec.get("require_all_complete", False),
        )
        items = []
        for j, item_spec in enumerate(spec.get("checklist_items", [])):
            items.append(ChecklistItemDefinition.create(
                template_id=template.id,
                title=item_spec["title"],
                is_required=item_spec.get("is_required", True),
                sort_order=j,
            ))
        template.set_checklist_items(items)
        subtypes = []
        for k, sub_spec in enumerate(spec.get("subtypes", [])):
            subtypes.append(WorkflowSubtype.create(
                template_id=template.id,
                name=sub_spec["name"],
                description=sub_spec.get("description"),
                sort_order=k,
            ))
        template.set_subtypes(subtypes)
        repo.save(template)


# ---------------------------------------------------------------------------
# Orchestrator: seed all data for a single company
# ---------------------------------------------------------------------------

def seed_company_data(session, company_id: str, company_name: str = "Demo Company") -> dict:
    """Seed demo data for a single existing company.

    The company and its email domain(s) must already exist in the database.
    Creates departments, locations, users, asset types, assets, workflow templates,
    service requests, notifications, reports, custom fields, and custom field values.

    Returns ``{"admin_user_id": ..., "admin_email": ...}``.
    """
    # Resolve the company's email domain for user email generation
    domain_row = session.query(CompanyEmailDomainModel).filter_by(
        company_id=company_id,
    ).first()
    domain = domain_row.domain if domain_row else f"{company_name.lower().replace(' ', '')}.local"

    dept_map = seed_departments_for_company(session, company_id)
    loc_map = seed_locations_for_company(session, company_id)
    users = seed_users_for_company(session, company_id, domain, dept_map)
    seed_asset_type_definitions_for_company(session, company_id)
    asset_ids = seed_assets_for_company(session, company_id, users, dept_map, loc_map)
    seed_workflow_templates_for_company(session, company_id)
    request_ids = seed_requests_for_company(session, company_id, users)
    seed_notifications_for_company(session, company_id, users)
    seed_reports_for_company(session, company_id, users)
    seed_custom_field_definitions_for_company(session, company_id)
    seed_custom_field_values_for_company(session, asset_ids, request_ids)
    session.flush()
    return {"admin_user_id": users["admin"][0]["id"], "admin_email": users["admin"][0]["email"]}


# ---------------------------------------------------------------------------
# Seed-script-only helpers (company creation, cleanup)
# ---------------------------------------------------------------------------

def clear_all(session):
    """Delete all data using TRUNCATE CASCADE for reliability."""
    from sqlalchemy import text

    print("Clearing existing data...")
    result = session.execute(text(
        "SELECT tablename FROM pg_tables "
        "WHERE schemaname = 'public' AND tablename != 'alembic_version'"
    ))
    tables = [row[0] for row in result]
    if tables:
        table_list = ", ".join(f'"{t}"' for t in tables)
        session.execute(text(f"TRUNCATE {table_list} CASCADE"))
        print(f"  Truncated {len(tables)} tables")
    session.commit()


def seed_companies(session) -> list[dict]:
    """Create companies with email domains. Returns list of {id, name, domain}."""
    companies = []
    for spec in COMPANIES:
        company = CompanyModel(
            id=uid(),
            name=spec["name"],
            status="active",
            is_active=True,
        )
        session.add(company)
        session.flush()

        for domain in spec["domains"]:
            session.add(CompanyEmailDomainModel(
                id=uid(),
                company_id=company.id,
                domain=domain,
            ))

        companies.append({
            "id": company.id,
            "name": spec["name"],
            "domain": spec["domains"][0],
        })
        print(f"  Company: {spec['name']} ({', '.join(spec['domains'])})")

    session.commit()
    return companies


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("DeskSupportMonkey — Seed Demo Data")
    print("=" * 60)
    print()

    session = SessionLocal()
    try:
        clear_all(session)
        print()

        print("Creating companies...")
        companies = seed_companies(session)
        print()

        # Super admin (no company)
        print("Creating super admin...")
        sa = UserModel(
            id=uid(),
            email="admin@desksupportmonkey.com",
            name="Platform Admin",
            role="super_admin",
            company_id=None,
            department_id=None,
            is_active=True,
        )
        session.add(sa)
        session.commit()
        print(f"  Super Admin: {sa.email}")
        print()

        # Seed per-company data via orchestrator
        company_results = {}
        for company in companies:
            print(f"Seeding data for {company['name']}...")
            result = seed_company_data(session, company["id"], company["name"])
            company_results[company["id"]] = result
            session.commit()
            print(f"  Done — admin: {result['admin_email']}")
            print()

        print("=" * 60)
        print("Seed complete!")
        print()
        print("Demo login emails:")
        print(f"  Super Admin:  {sa.email}")
        for company in companies:
            cid = company["id"]
            print(f"\n  {company['name']}:")
            print(f"    Admin: {company_results[cid]['admin_email']}")
        print()
        print("Use magic link auth — check Mailpit at http://localhost:8028")
        print("=" * 60)

    except Exception as e:
        session.rollback()
        print(f"\nError: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    main()
