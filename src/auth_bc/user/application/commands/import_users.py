import csv
import io
import re
from dataclasses import dataclass, field
from typing import Optional

from src.auth_bc.user.domain.entities import User
from src.auth_bc.user.domain.enums import UserRole
from src.auth_bc.user.domain.repository import UserRepositoryInterface
from src.company_bc.company.domain.repository import CompanyRepositoryInterface
from src.company_bc.department.domain.entities import Department
from src.company_bc.department.domain.repository import DepartmentRepositoryInterface


REQUIRED_HEADERS = {"email"}
OPTIONAL_HEADERS = {"name", "role", "department"}
ALL_HEADERS = REQUIRED_HEADERS | OPTIONAL_HEADERS

VALID_ROLES = {"employee", "technician", "admin"}

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class InvalidCSVError(Exception):
    pass


@dataclass
class ImportRowError:
    row: int
    error: str


@dataclass
class DepartmentInfo:
    id: str
    name: str


@dataclass
class PreviewResult:
    total_rows: int
    valid_rows: int
    errors: list[ImportRowError] = field(default_factory=list)
    unknown_departments: list[str] = field(default_factory=list)
    existing_departments: list[DepartmentInfo] = field(default_factory=list)


@dataclass
class ImportResult:
    total: int
    successful: int
    failed: list[ImportRowError] = field(default_factory=list)
    departments_created: list[str] = field(default_factory=list)
    invitations_sent: int = 0


class ImportUsersService:
    def __init__(
        self,
        user_repo: UserRepositoryInterface,
        department_repo: DepartmentRepositoryInterface,
        company_repo: CompanyRepositoryInterface,
    ):
        self.user_repo = user_repo
        self.department_repo = department_repo
        self.company_repo = company_repo

    def preview(self, csv_content: str, company_id: str) -> PreviewResult:
        rows, _ = self._parse_csv(csv_content)

        company = self.company_repo.find_by_id(company_id)
        if not company:
            raise InvalidCSVError("Company not found")
        allowed_domains = [d.lower() for d in company.email_domains]

        errors: list[ImportRowError] = []
        seen_emails: set[str] = set()
        department_names: set[str] = set()

        for idx, row in enumerate(rows, start=2):
            row = self._normalize_row(row)
            error = self._validate_row(row, seen_emails, allowed_domains, company_id)
            if error:
                errors.append(ImportRowError(row=idx, error=error))
            else:
                seen_emails.add(row["email"].lower())

            dept = row.get("department", "").strip()
            if dept:
                department_names.add(dept)

        # Resolve departments
        unknown: list[str] = []
        existing: list[DepartmentInfo] = []
        seen_dept_names: set[str] = set()
        for name in sorted(department_names):
            dept = self.department_repo.find_by_name(name, company_id)
            if dept:
                if dept.name.lower() not in seen_dept_names:
                    existing.append(DepartmentInfo(id=dept.id, name=dept.name))
                    seen_dept_names.add(dept.name.lower())
            else:
                unknown.append(name)

        return PreviewResult(
            total_rows=len(rows),
            valid_rows=len(rows) - len(errors),
            errors=errors,
            unknown_departments=unknown,
            existing_departments=existing,
        )

    def confirm(
        self,
        csv_content: str,
        company_id: str,
        performed_by: str,
        department_mapping: dict,
        magic_link_sender: Optional[object] = None,
    ) -> ImportResult:
        rows, _ = self._parse_csv(csv_content)

        company = self.company_repo.find_by_id(company_id)
        if not company:
            raise InvalidCSVError("Company not found")
        allowed_domains = [d.lower() for d in company.email_domains]

        # Process department mapping: create new departments first
        departments_created: list[str] = []
        dept_name_to_id: dict[str, str] = {}

        for dept_name, mapping in department_mapping.items():
            action = mapping.get("action", "")
            if action == "create":
                new_dept = Department.create(company_id=company_id, name=dept_name)
                self.department_repo.save(new_dept)
                dept_name_to_id[dept_name.lower()] = new_dept.id
                departments_created.append(dept_name)
            elif action == "map":
                dept_id = mapping.get("department_id", "")
                if dept_id:
                    dept_name_to_id[dept_name.lower()] = dept_id

        errors: list[ImportRowError] = []
        seen_emails: set[str] = set()
        users_to_save: list[User] = []
        invitations: list[str] = []

        for idx, row in enumerate(rows, start=2):
            row = self._normalize_row(row)
            error = self._validate_row(row, seen_emails, allowed_domains, company_id)
            if error:
                errors.append(ImportRowError(row=idx, error=error))
                continue

            email = row["email"].lower().strip()
            seen_emails.add(email)

            # Check if user already exists
            existing_user = self.user_repo.find_by_email(email)
            if existing_user:
                if existing_user.company_id != company_id:
                    errors.append(ImportRowError(row=idx, error="User belongs to another company"))
                    continue
                errors.append(ImportRowError(row=idx, error="User already exists"))
                continue

            # Resolve role
            role_str = row.get("role", "").strip().lower()
            role = UserRole(role_str) if role_str in VALID_ROLES else UserRole.EMPLOYEE

            # Resolve department
            department_id = None
            dept_name = row.get("department", "").strip()
            if dept_name:
                # Check mapping first
                if dept_name.lower() in dept_name_to_id:
                    department_id = dept_name_to_id[dept_name.lower()]
                else:
                    # Try existing departments
                    dept = self.department_repo.find_by_name(dept_name, company_id)
                    if dept:
                        department_id = dept.id
                        dept_name_to_id[dept_name.lower()] = dept.id

            name = row.get("name", "").strip() or None
            user = User.create(
                email=email,
                role=role,
                company_id=company_id,
                name=name,
                department_id=department_id,
            )
            users_to_save.append(user)
            invitations.append(email)

        # Save all users
        for user in users_to_save:
            self.user_repo.save(user)

        # Send magic link invitations
        invitations_sent = 0
        if magic_link_sender:
            for email in invitations:
                try:
                    magic_link_sender(email)  # type: ignore[operator]
                    invitations_sent += 1
                except Exception:
                    pass  # Don't fail import for invitation errors

        return ImportResult(
            total=len(rows),
            successful=len(users_to_save),
            failed=errors,
            departments_created=departments_created,
            invitations_sent=invitations_sent,
        )

    def _parse_csv(self, csv_content: str) -> tuple[list[dict], list[str]]:
        reader = csv.DictReader(io.StringIO(csv_content))
        if not reader.fieldnames:
            raise InvalidCSVError("CSV file is empty or has no headers")

        headers = {h.strip().lower() for h in reader.fieldnames}
        missing = REQUIRED_HEADERS - headers
        if missing:
            raise InvalidCSVError(f"Missing required columns: {', '.join(sorted(missing))}")

        rows = list(reader)
        if not rows:
            raise InvalidCSVError("CSV file has no data rows")

        return rows, list(headers)

    @staticmethod
    def _normalize_row(row: dict) -> dict:
        return {k.strip().lower(): (v.strip() if v else "") for k, v in row.items()}

    def _validate_row(
        self,
        row: dict,
        seen_emails: set[str],
        allowed_domains: list[str],
        company_id: str,
    ) -> Optional[str]:
        # Email required
        email = row.get("email", "").strip()
        if not email:
            return "email is required"

        # Email format
        if not EMAIL_RE.match(email):
            return "Invalid email format"

        # Domain check
        domain = email.split("@", 1)[-1].lower()
        if domain not in allowed_domains:
            return f"Email domain '{domain}' is not allowed for this company"

        # Duplicate in CSV
        if email.lower() in seen_emails:
            return f"Duplicate email '{email}' in CSV"

        # Role validation
        role = row.get("role", "").strip().lower()
        if role and role not in VALID_ROLES:
            return f"Invalid role '{row.get('role', '').strip()}'. Valid: {', '.join(sorted(VALID_ROLES))}"

        return None
