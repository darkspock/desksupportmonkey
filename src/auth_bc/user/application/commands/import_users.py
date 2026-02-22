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
from src.company_bc.employee_role.domain.entities import EmployeeRole
from src.company_bc.employee_role.domain.repository import EmployeeRoleRepositoryInterface


REQUIRED_HEADERS = {"email"}
OPTIONAL_HEADERS = {"name", "role", "department", "employee_role"}
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
class NameIdInfo:
    id: str
    name: str


# Keep backward-compatible alias
DepartmentInfo = NameIdInfo


@dataclass
class PreviewResult:
    total_rows: int
    valid_rows: int
    new_users: int = 0
    existing_users: int = 0
    errors: list[ImportRowError] = field(default_factory=list)
    unknown_departments: list[str] = field(default_factory=list)
    existing_departments: list[NameIdInfo] = field(default_factory=list)
    unknown_employee_roles: list[str] = field(default_factory=list)
    existing_employee_roles: list[NameIdInfo] = field(default_factory=list)


@dataclass
class ImportResult:
    total: int
    successful: int
    updated: int = 0
    failed: list[ImportRowError] = field(default_factory=list)
    departments_created: list[str] = field(default_factory=list)
    employee_roles_created: list[str] = field(default_factory=list)
    invitations_sent: int = 0


class ImportUsersService:
    def __init__(
        self,
        user_repo: UserRepositoryInterface,
        department_repo: DepartmentRepositoryInterface,
        company_repo: CompanyRepositoryInterface,
        employee_role_repo: Optional[EmployeeRoleRepositoryInterface] = None,
    ):
        self.user_repo = user_repo
        self.department_repo = department_repo
        self.company_repo = company_repo
        self.employee_role_repo = employee_role_repo

    def preview(self, csv_content: str, company_id: str) -> PreviewResult:
        rows, _ = self._parse_csv(csv_content)

        company = self.company_repo.find_by_id(company_id)
        if not company:
            raise InvalidCSVError("Company not found")
        allowed_domains = [d.lower() for d in company.email_domains]

        errors: list[ImportRowError] = []
        seen_emails: set[str] = set()
        department_names: set[str] = set()
        employee_role_names: set[str] = set()
        existing_user_count = 0

        for idx, row in enumerate(rows, start=2):
            row = self._normalize_row(row)
            error = self._validate_row(row, seen_emails, allowed_domains, company_id)
            if error:
                errors.append(ImportRowError(row=idx, error=error))
            else:
                email = row["email"].lower()
                seen_emails.add(email)
                existing_user = self.user_repo.find_by_email(email)
                if existing_user and existing_user.company_id == company_id:
                    existing_user_count += 1

            dept = row.get("department", "").strip()
            if dept:
                department_names.add(dept)

            emp_role = row.get("employee_role", "").strip()
            if emp_role:
                employee_role_names.add(emp_role)

        valid_count = len(rows) - len(errors)

        # Resolve departments: classify CSV values as known/unknown
        unknown_depts: list[str] = []
        for name in sorted(department_names):
            dept = self.department_repo.find_by_name(name, company_id)
            if not dept:
                unknown_depts.append(name)

        # Return ALL company departments for mapping
        all_depts, _ = self.department_repo.find_all(company_id, page=1, page_size=500)
        existing_depts = [NameIdInfo(id=d.id, name=d.name) for d in all_depts]

        # Resolve employee roles: classify CSV values as known/unknown
        unknown_roles: list[str] = []
        if self.employee_role_repo:
            for name in sorted(employee_role_names):
                role = self.employee_role_repo.find_by_name(name, company_id)
                if not role:
                    unknown_roles.append(name)

        # Return ALL company employee roles for mapping
        existing_roles: list[NameIdInfo] = []
        if self.employee_role_repo:
            all_roles, _ = self.employee_role_repo.find_all(company_id, page=1, page_size=500)
            existing_roles = [NameIdInfo(id=r.id, name=r.name) for r in all_roles]

        return PreviewResult(
            total_rows=len(rows),
            valid_rows=valid_count,
            new_users=valid_count - existing_user_count,
            existing_users=existing_user_count,
            errors=errors,
            unknown_departments=unknown_depts,
            existing_departments=existing_depts,
            unknown_employee_roles=unknown_roles,
            existing_employee_roles=existing_roles,
        )

    def confirm(
        self,
        csv_content: str,
        company_id: str,
        performed_by: str,
        department_mapping: dict,
        employee_role_mapping: Optional[dict] = None,
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

        # Process employee role mapping: create new roles first
        employee_roles_created: list[str] = []
        role_name_to_id: dict[str, str] = {}

        for role_name, mapping in (employee_role_mapping or {}).items():
            action = mapping.get("action", "")
            if action == "create" and self.employee_role_repo:
                new_role = EmployeeRole.create(company_id=company_id, name=role_name)
                self.employee_role_repo.save(new_role)
                role_name_to_id[role_name.lower()] = new_role.id
                employee_roles_created.append(role_name)
            elif action == "map":
                role_id = mapping.get("employee_role_id", "")
                if role_id:
                    role_name_to_id[role_name.lower()] = role_id

        errors: list[ImportRowError] = []
        seen_emails: set[str] = set()
        users_to_save: list[User] = []
        users_to_update: list[User] = []
        invitations: list[str] = []

        for idx, row in enumerate(rows, start=2):
            row = self._normalize_row(row)
            error = self._validate_row(row, seen_emails, allowed_domains, company_id)
            if error:
                errors.append(ImportRowError(row=idx, error=error))
                continue

            email = row["email"].lower().strip()
            seen_emails.add(email)

            # Resolve department
            department_id = self._resolve_department(row, dept_name_to_id, company_id)

            # Resolve employee role
            employee_role_id = self._resolve_employee_role(row, role_name_to_id, company_id)

            # Check if user already exists
            existing_user = self.user_repo.find_by_email(email)
            if existing_user:
                if existing_user.company_id != company_id:
                    errors.append(ImportRowError(row=idx, error="User belongs to another company"))
                    continue
                # Update existing user
                name = row.get("name", "").strip() or None
                if name:
                    existing_user.name = name
                existing_user.assign_department(department_id)
                existing_user.assign_employee_role(employee_role_id)
                users_to_update.append(existing_user)
                continue

            # Resolve role
            role_str = row.get("role", "").strip().lower()
            role = UserRole(role_str) if role_str in VALID_ROLES else UserRole.EMPLOYEE

            name = row.get("name", "").strip() or None
            user = User.create(
                email=email,
                role=role,
                company_id=company_id,
                name=name,
                department_id=department_id,
            )
            if employee_role_id:
                user.assign_employee_role(employee_role_id)
            users_to_save.append(user)
            invitations.append(email)

        # Save new users
        for user in users_to_save:
            self.user_repo.save(user)

        # Update existing users
        for user in users_to_update:
            self.user_repo.save(user)

        # Send magic link invitations (only for new users)
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
            updated=len(users_to_update),
            failed=errors,
            departments_created=departments_created,
            employee_roles_created=employee_roles_created,
            invitations_sent=invitations_sent,
        )

    def _resolve_department(
        self, row: dict, dept_name_to_id: dict[str, str], company_id: str
    ) -> Optional[str]:
        dept_name = row.get("department", "").strip()
        if not dept_name:
            return None
        if dept_name.lower() in dept_name_to_id:
            return dept_name_to_id[dept_name.lower()]
        dept = self.department_repo.find_by_name(dept_name, company_id)
        if dept:
            dept_name_to_id[dept_name.lower()] = dept.id
            return dept.id
        return None

    def _resolve_employee_role(
        self, row: dict, role_name_to_id: dict[str, str], company_id: str
    ) -> Optional[str]:
        emp_role_name = row.get("employee_role", "").strip()
        if not emp_role_name:
            return None
        if emp_role_name.lower() in role_name_to_id:
            return role_name_to_id[emp_role_name.lower()]
        if self.employee_role_repo:
            emp_role = self.employee_role_repo.find_by_name(emp_role_name, company_id)
            if emp_role:
                role_name_to_id[emp_role_name.lower()] = emp_role.id
                return emp_role.id
        return None

    def _parse_csv(self, csv_content: str) -> tuple[list[dict], list[str]]:
        try:
            dialect: csv.Dialect | type[csv.Dialect] = csv.Sniffer().sniff(
                csv_content[:2048], delimiters=",;\t"
            )
        except csv.Error:
            dialect = csv.excel
        reader = csv.DictReader(io.StringIO(csv_content), dialect=dialect)
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
