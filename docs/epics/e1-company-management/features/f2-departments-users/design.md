# Design: F2 - Departments + User Management

**Feature:** [requirements.md](requirements.md)
**Date:** 2026-02-15

---

## Architecture Overview

F2 introduces the `department` sub-domain within `company_bc` and adds user management endpoints. All tenant-scoped endpoints use `company_id` from tenant context.

```
NEW FILES:
src/company_bc/department/
├── domain/
│   ├── entities.py           # Department entity
│   └── repository.py         # DepartmentRepositoryInterface
├── application/
│   ├── commands/
│   │   ├── create_department.py
│   │   ├── update_department.py
│   │   └── delete_department.py
│   └── queries/
│       ├── list_departments.py
│       └── get_department.py
└── infrastructure/
    ├── models.py             # DepartmentModel
    └── repository.py         # DepartmentRepository

adapters/http/api/departments/
├── routers.py
└── schemas.py

adapters/http/api/users/
├── routers.py
└── schemas.py

MODIFIED FILES:
src/auth_bc/user/infrastructure/models.py     # Add department_id column
src/auth_bc/user/domain/entities.py           # Add department_id field
src/auth_bc/user/infrastructure/repository.py # Add query methods for user management
src/auth_bc/user/domain/repository.py         # Add interface methods
core/models_registry.py                       # Add DepartmentModel
app.py                                        # Register new routers
```

---

## Domain Layer

### Department Entity

```python
@dataclass
class Department:
    id: str
    company_id: str
    name: str
    is_active: bool
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    @classmethod
    def create(cls, company_id: str, name: str) -> "Department":
        if not name or not name.strip():
            raise ValueError("Department name is required")
        return cls(
            id=str(ulid.new()),
            company_id=company_id,
            name=name.strip(),
            is_active=True,
        )

    def deactivate(self) -> None:
        self.is_active = False

    def update_name(self, name: str) -> None:
        if not name or not name.strip():
            raise ValueError("Department name is required")
        self.name = name.strip()
```

### DepartmentRepositoryInterface

```python
class DepartmentRepositoryInterface(ABC):
    def save(self, department: Department) -> Department: ...
    def find_by_id(self, department_id: str, company_id: str) -> Optional[Department]: ...
    def find_by_name(self, name: str, company_id: str) -> Optional[Department]: ...
    def find_all(self, company_id: str, page: int, page_size: int, include_inactive: bool) -> tuple[list[Department], int]: ...
    def count_users(self, department_id: str) -> int: ...
```

### User Entity (extend)

Add `department_id: Optional[str] = None` field.

Add methods:
```python
def activate(self) -> None:
    self.is_active = True

def assign_department(self, department_id: Optional[str]) -> None:
    self.department_id = department_id
```

### UserRepositoryInterface (extend)

Add methods:
```python
def find_all_by_company(self, company_id: str, page: int, page_size: int,
                         role: Optional[str], is_active: Optional[bool],
                         department_id: Optional[str], search: Optional[str]) -> tuple[list[User], int]: ...
def find_by_id_and_company(self, user_id: str, company_id: str) -> Optional[User]: ...
def count_by_department(self, department_id: str) -> int: ...
```

---

## Infrastructure Layer

### DepartmentModel (NEW)

```python
class DepartmentModel(ULIDMixin, TimestampMixin, Base):
    __tablename__ = "departments"
    company_id = Column(String(26), ForeignKey("companies.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    __table_args__ = (
        UniqueConstraint("company_id", "name", name="uq_department_company_name"),
    )
```

### UserModel (EXTEND)

```python
department_id = Column(String(26), ForeignKey("departments.id"), nullable=True, index=True)
```

### DepartmentRepository

Standard CRUD implementation:
- `find_by_id()`: filter by `id` AND `company_id` (tenant isolation at repo level)
- `find_by_name()`: case-insensitive match within company
- `find_all()`: pagination, optional `include_inactive` filter
- `count_users()`: COUNT from users where department_id matches

### UserRepository (EXTEND)

Add:
- `find_all_by_company()`: filters by company_id + optional role/is_active/department_id/search, pagination
- `find_by_id_and_company()`: ensures tenant isolation
- `count_by_department()`: for department user count
- Update `save()` to include `department_id`
- Update `_to_entity()` to include `department_id`

---

## Application Layer

### Department Commands

**CreateDepartmentCommand:**
1. Validate name uniqueness within company → `DepartmentNameExistsError`
2. Create entity, save
3. Return department

**UpdateDepartmentCommand:**
1. Find department (by id + company_id) → `DepartmentNotFoundError`
2. Validate name uniqueness (exclude self) → `DepartmentNameExistsError`
3. Update name, save
4. Return department

**DeleteDepartmentCommand:**
1. Find department → `DepartmentNotFoundError`
2. Check user count → `DepartmentHasUsersError` if > 0
3. Deactivate (soft delete), save
4. Return department

### Department Queries

**ListDepartmentsQuery:** page, page_size, include_inactive → (departments, total)
**GetDepartmentQuery:** department_id → department with user_count

### User Management Commands

These go in `src/auth_bc/user/application/commands/`:

**ChangeUserRoleCommand:**
1. Find user by id + company_id → `UserNotFoundError`
2. Validate not changing own role → `CannotChangeSelfError`
3. Validate target role is not super_admin → `CannotAssignSuperAdminError`
4. Change role, save
5. Return user

**DeactivateUserCommand:**
1. Find user by id + company_id → `UserNotFoundError`
2. Validate not deactivating self → `CannotDeactivateSelfError`
3. Deactivate, save
4. Return user

**ActivateUserCommand:**
1. Find user by id + company_id → `UserNotFoundError`
2. Activate, save
3. Return user

**AssignDepartmentCommand:**
1. Find user by id + company_id → `UserNotFoundError`
2. If department_id is not null:
   a. Find department → `DepartmentNotFoundError`
   b. Validate same company → `DepartmentNotFoundError`
   c. Validate is_active → `DepartmentInactiveError`
3. Assign department, save
4. Return user

### User Queries

**ListUsersQuery:** page, page_size, role, is_active, department_id, search → (users, total)
**GetUserQuery:** user_id, company_id → user

---

## HTTP Layer

### Department Schemas

```python
class CreateDepartmentRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)

class UpdateDepartmentRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)

class DepartmentResponse(BaseModel):
    id: str
    company_id: str
    name: str
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]

class DepartmentDetailResponse(DepartmentResponse):
    user_count: int
```

### Department Router

| Method | Path | Handler | Auth |
|---|---|---|---|
| POST | /api/v1/departments | create_department | admin+ |
| GET | /api/v1/departments | list_departments | admin+ |
| GET | /api/v1/departments/{id} | get_department | admin+ |
| PUT | /api/v1/departments/{id} | update_department | admin+ |
| DELETE | /api/v1/departments/{id} | delete_department | admin+ |

All use `Depends(require_role(UserRole.ADMIN))`. Company_id from tenant context.

### User Schemas

```python
class ChangeRoleRequest(BaseModel):
    role: str  # validated against UserRole values, excluding super_admin

class AssignDepartmentRequest(BaseModel):
    department_id: Optional[str]

class UserDetailResponse(BaseModel):
    id: str
    email: str
    name: Optional[str]
    role: str
    company_id: Optional[str]
    department_id: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]

class UserListParams(BaseModel):
    page: int = 1
    page_size: int = 20
    role: Optional[str] = None
    is_active: Optional[bool] = None
    department_id: Optional[str] = None
    search: Optional[str] = None
```

### User Router

| Method | Path | Handler | Auth |
|---|---|---|---|
| GET | /api/v1/users | list_users | admin+ |
| GET | /api/v1/users/{id} | get_user | admin+ |
| PATCH | /api/v1/users/{id}/role | change_role | admin+ |
| PATCH | /api/v1/users/{id}/deactivate | deactivate_user | admin+ |
| PATCH | /api/v1/users/{id}/activate | activate_user | admin+ |
| PATCH | /api/v1/users/{id}/department | assign_department | admin+ |

All use `Depends(require_role(UserRole.ADMIN))`. Company_id from tenant context.

---

## Migration

Alembic migration:
1. Create `departments` table with UNIQUE(company_id, name) constraint
2. Add `department_id` column to `users` table (nullable FK to departments.id)

---

## Decisions

1. **Tenant isolation at repository level**: All department queries filter by `company_id`. User management queries use `find_by_id_and_company()` to ensure admin can't access users in other companies.

2. **Department soft delete blocks if users assigned**: Admin must explicitly reassign users before deleting a department. This prevents accidental data loss.

3. **User role change cannot target super_admin**: This is enforced in both domain entity and HTTP layer (defense in depth).

4. **Admin cannot modify themselves**: Both role change and deactivation check if target user_id == current user_id.

5. **Department assignment validates company match**: Even though department_id is a FK, we explicitly check that the department belongs to the same company as the user.
