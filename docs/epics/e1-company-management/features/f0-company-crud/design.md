# Design: F0 - Company CRUD + Email Domains

**Feature:** [requirements.md](requirements.md)
**Date:** 2026-02-15

---

## Architecture Overview

F0 extends the `company_bc` bounded context with full CRUD and introduces the `CompanyEmailDomain` entity. It also updates `auth_bc` to replace the domain matching stub.

```
src/company_bc/company/
├── domain/
│   ├── entities.py           # Company entity with status, CompanyEmailDomain entity
│   ├── enums.py              # CompanyStatus enum
│   └── repository.py         # CompanyRepositoryInterface
├── application/
│   ├── commands/
│   │   ├── create_company.py # CreateCompanyCommand + Handler
│   │   └── update_company.py # UpdateCompanyCommand + Handler
│   └── queries/
│       ├── list_companies.py # ListCompaniesQuery + Handler
│       └── get_company.py    # GetCompanyQuery + Handler
└── infrastructure/
    ├── models.py             # CompanyModel (extend), CompanyEmailDomainModel (new)
    └── repository.py         # CompanyRepository

adapters/http/api/companies/
├── routers.py                # Company CRUD endpoints
└── schemas.py                # Request/response Pydantic models

src/auth_bc/company_lookup/infrastructure/service.py  # Replace stub
```

---

## Domain Layer

### CompanyStatus Enum

```python
class CompanyStatus(str, Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DEACTIVATED = "deactivated"
```

### Company Entity

```python
@dataclass
class Company:
    id: str
    name: str
    status: CompanyStatus
    email_domains: list[str]   # domain strings
    is_active: bool
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    @classmethod
    def create(cls, name: str, email_domains: list[str]) -> "Company":
        # Validate name not empty, domains not empty, lowercase domains
        return cls(
            id=str(ulid.new()),
            name=name.strip(),
            status=CompanyStatus.ACTIVE,
            email_domains=[d.lower().strip() for d in email_domains],
            is_active=True,
        )
```

### CompanyRepositoryInterface

```python
class CompanyRepositoryInterface(ABC):
    def save(self, company: Company) -> Company: ...
    def find_by_id(self, company_id: str) -> Optional[Company]: ...
    def find_by_name(self, name: str) -> Optional[Company]: ...
    def find_all(self, page: int, page_size: int, search: Optional[str]) -> tuple[list[Company], int]: ...
    def find_domain(self, domain: str) -> Optional[str]: ...  # returns company_id
    def find_domains_by_company(self, company_id: str) -> list[str]: ...
    def save_domains(self, company_id: str, domains: list[str]) -> None: ...
    def count_users(self, company_id: str) -> int: ...
    def count_departments(self, company_id: str) -> int: ...
```

---

## Infrastructure Layer

### CompanyEmailDomainModel (NEW)

```python
class CompanyEmailDomainModel(ULIDMixin, Base):
    __tablename__ = "company_email_domains"
    company_id = Column(String(26), ForeignKey("companies.id"), nullable=False, index=True)
    domain = Column(String(255), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
```

### CompanyModel (EXTEND)

Add `status` column:
```python
status = Column(String(20), nullable=False, server_default="active")
```

Add relationship:
```python
email_domains = relationship("CompanyEmailDomainModel", backref="company", cascade="all, delete-orphan")
```

### CompanyRepository

Key implementation notes:
- `save()`: upsert pattern (same as UserRepository)
- `find_all()`: uses `.offset()` / `.limit()` for pagination, `.ilike()` for search
- `save_domains()`: delete all existing domains for company, insert new ones (full replacement)
- `find_domain()`: query CompanyEmailDomainModel, join Company to check is_active
- `count_users()`: `SELECT COUNT(*) FROM users WHERE company_id = ?`
- `count_departments()`: `SELECT COUNT(*) FROM departments WHERE company_id = ? AND is_active = true` (will return 0 until F2 creates department table)

### CompanyLookupService (REPLACE STUB)

```python
def find_company_id_by_email_domain(self, email: str) -> Optional[str]:
    domain = self.extract_domain(email)
    result = (
        self.session.query(CompanyEmailDomainModel.company_id)
        .join(CompanyModel, CompanyEmailDomainModel.company_id == CompanyModel.id)
        .filter(CompanyEmailDomainModel.domain == domain)
        .filter(CompanyModel.is_active.is_(True))
        .first()
    )
    return result[0] if result else None
```

---

## Application Layer

### CreateCompanyCommand

```python
@dataclass
class CreateCompanyCommand:
    name: str
    email_domains: list[str]
    admin_email: Optional[str] = None
```

Handler logic:
1. Validate name uniqueness → `find_by_name(name)` → 409 if exists
2. Validate each domain uniqueness → `find_domain(domain)` → 409 if exists
3. Create Company entity
4. Save company
5. Save domains
6. If admin_email:
   a. Check user doesn't exist → `user_repo.find_by_email(admin_email)` → 409 if exists
   b. Create User entity with admin role
   c. Save user
   d. Create magic link and send email
7. Return company

### UpdateCompanyCommand

```python
@dataclass
class UpdateCompanyCommand:
    company_id: str
    name: Optional[str] = None
    email_domains: Optional[list[str]] = None
```

Handler logic:
1. Find company → 404 if not found
2. If name changed: validate uniqueness (exclude current company) → 409 if conflict
3. If domains changed: validate each domain uniqueness (exclude current company's domains) → 409 if conflict
4. Update company entity
5. Save company
6. If domains changed: save_domains (full replacement)
7. Return updated company

### ListCompaniesQuery

```python
@dataclass
class ListCompaniesQuery:
    page: int = 1
    page_size: int = 20
    search: Optional[str] = None
```

### GetCompanyQuery

```python
@dataclass
class GetCompanyQuery:
    company_id: str
```

Returns company with user_count and department_count.

---

## HTTP Layer

### Schemas

```python
class CreateCompanyRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    email_domains: list[str] = Field(min_length=1)
    admin_email: Optional[EmailStr] = None

class UpdateCompanyRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    email_domains: Optional[list[str]] = Field(None, min_length=1)

class CompanyResponse(BaseModel):
    id: str
    name: str
    status: str
    email_domains: list[str]
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]

class CompanyDetailResponse(CompanyResponse):
    user_count: int
    department_count: int
```

### Router

| Method | Path | Handler | Auth |
|---|---|---|---|
| POST | /api/v1/companies | create_company | super_admin |
| GET | /api/v1/companies | list_companies | super_admin |
| GET | /api/v1/companies/{id} | get_company | super_admin |
| PUT | /api/v1/companies/{id} | update_company | super_admin |

All endpoints use `Depends(require_role(UserRole.SUPER_ADMIN))`.

---

## Migration

Single Alembic migration:
1. Add `status` column to `companies` table (String(20), NOT NULL, server_default="active")
2. Create `company_email_domains` table
3. Add indexes

---

## Decisions

1. **Domain list is fully replaced on update** (not additive). Simpler to implement and reason about. The PUT semantics mean "this is the complete list of domains."
2. **Department count returns 0** until F2 creates the department table. The query handles this gracefully (no table = 0).
3. **Company name uniqueness is case-insensitive**: compare with `.ilike()` or store lowercase.
4. **is_active stays in sync with status**: `is_active = (status == "active")`. Updated whenever status changes.
