from typing import Optional

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from src.auth_bc.user.domain.entities import User
from src.auth_bc.user.domain.enums import UserRole
from src.auth_bc.user.domain.repository import UserRepositoryInterface
from src.auth_bc.user.infrastructure.models import UserModel


class UserRepository(UserRepositoryInterface):
    def __init__(self, session: Session):
        self.session = session

    def save(self, user: User) -> User:
        existing = self.session.execute(
            select(UserModel).where(UserModel.id == user.id)
        ).scalar_one_or_none()
        if existing:
            existing.email = user.email
            existing.name = user.name
            existing.role = user.role.value
            existing.company_id = user.company_id
            existing.department_id = user.department_id
            existing.employee_role_id = user.employee_role_id
            existing.is_active = user.is_active
            existing.password_hash = user.password_hash
        else:
            model = UserModel(
                id=user.id,
                email=user.email,
                name=user.name,
                role=user.role.value,
                company_id=user.company_id,
                department_id=user.department_id,
                employee_role_id=user.employee_role_id,
                is_active=user.is_active,
                password_hash=user.password_hash,
            )
            self.session.add(model)
        self.session.flush()
        return user

    def find_by_id(self, user_id: str) -> Optional[User]:
        model = self.session.execute(
            select(UserModel).where(UserModel.id == user_id)
        ).scalar_one_or_none()
        return self._to_entity(model) if model else None

    def find_by_ids(self, user_ids: list[str]) -> dict[str, User]:
        if not user_ids:
            return {}
        unique_ids = list(set(user_ids))
        models = self.session.execute(
            select(UserModel).where(UserModel.id.in_(unique_ids))
        ).scalars().all()
        return {m.id: self._to_entity(m) for m in models}

    def find_by_email(self, email: str) -> Optional[User]:
        model = self.session.execute(
            select(UserModel).where(UserModel.email == email.lower().strip())
        ).scalar_one_or_none()
        return self._to_entity(model) if model else None

    def find_all_by_company(
        self,
        company_id: str,
        page: int,
        page_size: int,
        role: Optional[str] = None,
        is_active: Optional[bool] = None,
        department_id: Optional[str] = None,
        search: Optional[str] = None,
    ) -> tuple[list[User], int]:
        stmt = select(UserModel).where(UserModel.company_id == company_id)
        if role is not None:
            stmt = stmt.where(UserModel.role == role)
        if is_active is not None:
            stmt = stmt.where(UserModel.is_active == is_active)
        if department_id is not None:
            stmt = stmt.where(UserModel.department_id == department_id)
        if search:
            pattern = f"%{search}%"
            stmt = stmt.where(
                or_(
                    UserModel.email.ilike(pattern),
                    UserModel.name.ilike(pattern),
                )
            )
        total = self.session.execute(
            select(func.count()).select_from(stmt.subquery())
        ).scalar()
        models = self.session.execute(
            stmt.order_by(UserModel.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).scalars().all()
        return [self._to_entity(m) for m in models], total or 0

    def find_by_id_and_company(self, user_id: str, company_id: str) -> Optional[User]:
        model = self.session.execute(
            select(UserModel).where(
                UserModel.id == user_id, UserModel.company_id == company_id
            )
        ).scalar_one_or_none()
        return self._to_entity(model) if model else None

    def count_by_department(self, department_id: str) -> int:
        return (
            self.session.execute(
                select(func.count()).select_from(UserModel)
                .where(UserModel.department_id == department_id)
            ).scalar()
        ) or 0

    def find_technician_ids_by_company(self, company_id: str) -> list[str]:
        tech_roles = [
            UserRole.TECHNICIAN.value,
            UserRole.ADMIN.value,
            UserRole.SUPER_ADMIN.value,
        ]
        result = self.session.execute(
            select(UserModel.id).where(
                UserModel.company_id == company_id,
                UserModel.role.in_(tech_roles),
                UserModel.is_active == True,  # noqa: E712
            )
        ).scalars().all()
        return list(result)

    def find_admins_by_company(self, company_id: str) -> list[User]:
        models = self.session.execute(
            select(UserModel).where(
                UserModel.company_id == company_id,
                UserModel.role == UserRole.ADMIN.value,
                UserModel.is_active == True,  # noqa: E712
            )
        ).scalars().all()
        return [self._to_entity(m) for m in models]

    def find_admin_ids_by_company(self, company_id: str) -> list[str]:
        result = self.session.execute(
            select(UserModel.id).where(
                UserModel.company_id == company_id,
                UserModel.role == UserRole.ADMIN.value,
                UserModel.is_active == True,  # noqa: E712
            )
        ).scalars().all()
        return list(result)

    def count_admins_by_company(self, company_id: str) -> int:
        return (
            self.session.execute(
                select(func.count()).select_from(UserModel)
                .where(
                    UserModel.company_id == company_id,
                    UserModel.role == UserRole.ADMIN.value,
                    UserModel.is_active == True,  # noqa: E712
                )
            ).scalar()
        ) or 0

    @staticmethod
    def _to_entity(model: UserModel) -> User:
        return User(
            id=model.id,
            email=model.email,
            name=model.name,
            role=UserRole(model.role),
            company_id=model.company_id,
            department_id=model.department_id,
            employee_role_id=model.employee_role_id,
            is_active=model.is_active,
            password_hash=model.password_hash,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
