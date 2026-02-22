"""
Seed script for DeskSupportMonkey demo data.

Creates realistic demo data across all tables:
- 3 companies with email domains
- 1 super admin + users per role per company
- Departments, assets, service requests, comments, notes, events, notifications, reports

Usage:
    PYTHONPATH=src python scripts/seed_demo_data.py

Idempotent: clears all existing data before seeding.
"""

import os
import sys
import random
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
from src.asset_bc.asset.infrastructure.models import AssetModel, AssetEventModel
from src.request_bc.request.infrastructure.models import (
    ServiceRequestModel, RequestEventModel, RequestCommentModel, RequestNoteModel,
)
from src.notification_bc.notification.infrastructure.models import NotificationModel
from src.report_bc.report.infrastructure.models import ReportModel


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

# ---------------------------------------------------------------------------
# Seed functions
# ---------------------------------------------------------------------------

def clear_all(session):
    """Delete all data in reverse FK order."""
    print("Clearing existing data...")
    for model in [
        NotificationModel, ReportModel,
        RequestNoteModel, RequestCommentModel, RequestEventModel, ServiceRequestModel,
        AssetEventModel, AssetModel,
        UserModel, DepartmentModel,
        CompanyEmailDomainModel, CompanyModel,
    ]:
        count = session.query(model).delete()
        if count:
            print(f"  Deleted {count} rows from {model.__tablename__}")
    session.commit()


def seed_companies(session) -> list[dict]:
    """Create companies with email domains. Returns list of {id, name, domains}."""
    companies = []
    for i, spec in enumerate(COMPANIES):
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


def seed_departments(session, companies: list[dict]) -> dict[str, list[dict]]:
    """Create departments per company. Returns {company_id: [{id, name}]}."""
    dept_map = {}
    for company in companies:
        depts = []
        for name in DEPARTMENTS:
            dept = DepartmentModel(
                id=uid(),
                company_id=company["id"],
                name=name,
                is_active=True,
            )
            session.add(dept)
            session.flush()
            depts.append({"id": dept.id, "name": name})
        dept_map[company["id"]] = depts
    session.commit()
    print(f"  Departments: {len(DEPARTMENTS)} per company ({len(DEPARTMENTS) * len(companies)} total)")
    return dept_map


def seed_users(session, companies: list[dict], dept_map: dict) -> dict:
    """Create users. Returns {company_id: {role: [user_dicts]}, 'super_admin': user_dict}."""
    name_idx = 0
    users = {}

    def next_name():
        nonlocal name_idx
        first = FIRST_NAMES[name_idx % len(FIRST_NAMES)]
        last = LAST_NAMES[name_idx % len(LAST_NAMES)]
        name_idx += 1
        return first, last

    # Super admin
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
    users["super_admin"] = {"id": sa.id, "email": sa.email, "name": sa.name}
    print(f"  Super Admin: {sa.email}")

    for company in companies:
        cid = company["id"]
        domain = company["domain"]
        depts = dept_map[cid]
        company_users: dict[str, list] = {"admin": [], "procurement_manager": [], "technician": [], "employee": []}

        # Admin
        first, last = next_name()
        admin = UserModel(
            id=uid(),
            email=f"{first.lower()}.{last.lower()}@{domain}",
            name=f"{first} {last}",
            role="admin",
            company_id=cid,
            department_id=depts[0]["id"],  # Engineering
            is_active=True,
        )
        session.add(admin)
        company_users["admin"].append({"id": admin.id, "email": admin.email, "name": admin.name})

        # Procurement Manager
        first, last = next_name()
        pm = UserModel(
            id=uid(),
            email=f"{first.lower()}.{last.lower()}@{domain}",
            name=f"{first} {last}",
            role="procurement_manager",
            company_id=cid,
            department_id=depts[0]["id"],  # Engineering
            is_active=True,
        )
        session.add(pm)
        company_users["procurement_manager"].append({"id": pm.id, "email": pm.email, "name": pm.name})

        # Technicians (2)
        for _ in range(2):
            first, last = next_name()
            tech = UserModel(
                id=uid(),
                email=f"{first.lower()}.{last.lower()}@{domain}",
                name=f"{first} {last}",
                role="technician",
                company_id=cid,
                department_id=depts[3]["id"],  # IT
                is_active=True,
            )
            session.add(tech)
            company_users["technician"].append({"id": tech.id, "email": tech.email, "name": tech.name})

        # Employees (5)
        for j in range(5):
            first, last = next_name()
            dept = depts[j % len(depts)]
            emp = UserModel(
                id=uid(),
                email=f"{first.lower()}.{last.lower()}@{domain}",
                name=f"{first} {last}",
                role="employee",
                company_id=cid,
                department_id=dept["id"],
                is_active=True,
            )
            session.add(emp)
            company_users["employee"].append({"id": emp.id, "email": emp.email, "name": emp.name})

        users[cid] = company_users
        print(f"  Users for {company['name']}: 1 admin, 1 procurement mgr, 2 techs, 5 employees")

    session.commit()
    return users


def seed_assets(session, companies: list[dict], users: dict, dept_map: dict) -> dict[str, list[str]]:
    """Create assets per company. Returns {company_id: [asset_ids]}."""
    asset_map = {}
    serial_counter = 1000

    for company in companies:
        cid = company["id"]
        depts = dept_map[cid]
        employees = users[cid]["employee"]
        technicians = users[cid]["technician"]
        all_assignable = employees + technicians
        asset_ids = []

        # Pick ~18 items from the catalog (some repeated types)
        catalog_items = random.choices(ASSET_CATALOG, k=18)

        for i, (atype, brand, model, serial_prefix) in enumerate(catalog_items):
            serial_counter += 1
            serial = f"{serial_prefix}-{serial_counter:06d}"

            # Decide status and assignment
            rand = random.random()
            if rand < 0.55:
                status = "assigned"
                assigned_to = all_assignable[i % len(all_assignable)]["id"]
            elif rand < 0.80:
                status = "in_stock"
                assigned_to = None
            elif rand < 0.93:
                status = "in_repair"
                assigned_to = None
            else:
                status = "decommissioned"
                assigned_to = None

            days_ago = random.randint(30, 365)
            purchase = past_date_only(days_ago)
            # Some assets with warranty expiring soon (for alerts testing)
            if i < 3:
                warranty = date.today() + timedelta(days=random.randint(5, 25))
            elif i < 6:
                warranty = date.today() + timedelta(days=random.randint(60, 365))
            else:
                warranty = purchase + timedelta(days=random.randint(365, 1095))

            asset = AssetModel(
                id=uid(),
                company_id=cid,
                type=atype,
                brand=brand,
                model=model,
                serial_number=serial,
                status=status,
                assigned_to=assigned_to,
                department_id=depts[i % len(depts)]["id"],
                purchase_date=purchase,
                warranty_expiration=warranty,
                notes=f"Demo asset #{i+1}" if i < 3 else None,
            )
            session.add(asset)
            session.flush()
            asset_ids.append(asset.id)

            # Asset events: created + assigned
            admin_id = users[cid]["admin"][0]["id"]
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

        asset_map[cid] = asset_ids
        print(f"  Assets for {company['name']}: {len(catalog_items)} assets")

    session.commit()
    return asset_map


def seed_requests(session, companies: list[dict], users: dict) -> dict[str, list[str]]:
    """Create service requests per company. Returns {company_id: [request_ids]}."""
    request_map = {}
    statuses_cycle = ["submitted", "in_review", "in_progress", "resolved", "resolved", "rejected",
                      "submitted", "in_progress", "resolved", "in_review", "in_progress", "resolved"]

    for company in companies:
        cid = company["id"]
        employees = users[cid]["employee"]
        technicians = users[cid]["technician"]
        request_ids = []

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
                company_id=cid,
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

            # Request event: created
            session.add(RequestEventModel(
                id=uid(),
                request_id=request.id,
                event_type="request.created",
                data={"type": rtype, "title": title, "priority": priority},
                performed_by=created_by,
            ))

            # Status change events
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

            # Comments on ~60% of requests
            if random.random() < 0.6:
                comment_text = random.choice(COMMENT_TEMPLATES)
                session.add(RequestCommentModel(
                    id=uid(),
                    request_id=request.id,
                    author_id=created_by,
                    body=comment_text,
                ))
                # Technician reply on some
                if assigned_to and random.random() < 0.5:
                    session.add(RequestCommentModel(
                        id=uid(),
                        request_id=request.id,
                        author_id=assigned_to,
                        body="We're looking into this. I'll update you shortly.",
                    ))

            # Internal notes on ~40% of assigned requests
            if assigned_to and random.random() < 0.4:
                note_text = random.choice(NOTE_TEMPLATES)
                session.add(RequestNoteModel(
                    id=uid(),
                    request_id=request.id,
                    author_id=assigned_to,
                    body=note_text,
                ))

        request_map[cid] = request_ids
        print(f"  Requests for {company['name']}: {len(templates)} requests")

    session.commit()
    return request_map


def seed_notifications(session, companies: list[dict], users: dict):
    """Create notifications for all users."""
    total = 0
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

    for company in companies:
        cid = company["id"]
        all_users = (
            users[cid]["admin"] + users[cid]["procurement_manager"] + users[cid]["technician"] + users[cid]["employee"]
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
                    company_id=cid,
                    event_type=event_type,
                    title=title,
                    body=body,
                    data={"demo": True},
                    is_read=is_read,
                ))
                total += 1

    session.commit()
    print(f"  Notifications: {total} total")


def seed_reports(session, companies: list[dict], users: dict):
    """Create report records per company."""
    report_types = ["asset_inventory", "request_summary", "technician_performance"]
    statuses = ["completed", "pending", "failed"]
    total = 0

    for company in companies:
        cid = company["id"]
        admin_id = users[cid]["admin"][0]["id"]

        for i, rtype in enumerate(report_types):
            status = statuses[i]
            report = ReportModel(
                id=uid(),
                company_id=cid,
                requested_by=admin_id,
                type=rtype,
                status=status,
                parameters={"demo": True},
                storage_key=f"reports/{cid}/{rtype}.pdf" if status == "completed" else None,
                error_message="Simulated failure for demo" if status == "failed" else None,
                completed_at=past_date(5) if status == "completed" else None,
            )
            session.add(report)
            total += 1

    session.commit()
    print(f"  Reports: {total} total")


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

        print("Creating departments...")
        dept_map = seed_departments(session, companies)
        print()

        print("Creating users...")
        users = seed_users(session, companies, dept_map)
        print()

        print("Creating assets...")
        seed_assets(session, companies, users, dept_map)
        print()

        print("Creating service requests...")
        seed_requests(session, companies, users)
        print()

        print("Creating notifications...")
        seed_notifications(session, companies, users)
        print()

        print("Creating reports...")
        seed_reports(session, companies, users)
        print()

        print("=" * 60)
        print("Seed complete!")
        print()
        print("Demo login emails:")
        print(f"  Super Admin:  {users['super_admin']['email']}")
        for company in companies:
            cid = company["id"]
            print(f"\n  {company['name']}:")
            print(f"    Admin:      {users[cid]['admin'][0]['email']}")
            print(f"    Technician: {users[cid]['technician'][0]['email']}")
            print(f"    Employee:   {users[cid]['employee'][0]['email']}")
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
