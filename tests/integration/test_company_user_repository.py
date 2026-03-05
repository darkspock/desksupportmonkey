"""Integration tests for CompanyUserRepository (TASK-030)."""

import pytest
from sqlalchemy.exc import IntegrityError

from src.auth_bc.company_user.domain.entities import CompanyUser
from src.auth_bc.company_user.infrastructure.repository import CompanyUserRepository
from src.auth_bc.user.domain.enums import UserRole


class TestCompanyUserRepositorySave:
    def test_save_insert(self, db_session, admin_user, company):
        repo = CompanyUserRepository(db_session)
        cu = CompanyUser.create(
            user_id=admin_user.id,
            company_id=company.id,
            role=UserRole.ADMIN,
            department_id=None,
        )
        result = repo.save(cu)

        assert result.id == cu.id
        found = repo.find_by_user_and_company(admin_user.id, company.id)
        assert found is not None
        assert found.role == UserRole.ADMIN

    def test_save_update(self, db_session, admin_user, company):
        repo = CompanyUserRepository(db_session)
        cu = CompanyUser.create(
            user_id=admin_user.id, company_id=company.id, role=UserRole.ADMIN,
        )
        repo.save(cu)

        cu.change_role(UserRole.TECHNICIAN)
        repo.save(cu)

        found = repo.find_by_user_and_company(admin_user.id, company.id)
        assert found is not None
        assert found.role == UserRole.TECHNICIAN


class TestCompanyUserRepositoryFind:
    def test_find_by_user_and_company_found(self, db_session, admin_user, company):
        repo = CompanyUserRepository(db_session)
        cu = CompanyUser.create(
            user_id=admin_user.id, company_id=company.id, role=UserRole.ADMIN,
        )
        repo.save(cu)

        found = repo.find_by_user_and_company(admin_user.id, company.id)
        assert found is not None
        assert found.user_id == admin_user.id
        assert found.company_id == company.id

    def test_find_by_user_and_company_not_found(self, db_session):
        repo = CompanyUserRepository(db_session)
        found = repo.find_by_user_and_company("nonexistent", "nonexistent")
        assert found is None

    def test_find_by_user_id(self, db_session, company, make_user):
        repo = CompanyUserRepository(db_session)
        user = make_user(email="multi@testco.com", company_id=company.id)

        cu1 = CompanyUser.create(
            user_id=user.id, company_id=company.id, role=UserRole.EMPLOYEE,
        )
        repo.save(cu1)

        results = repo.find_by_user_id(user.id)
        assert len(results) == 1
        assert results[0].user_id == user.id

    def test_find_active_by_user_id(self, db_session, company, make_user):
        repo = CompanyUserRepository(db_session)
        user = make_user(email="active-test@testco.com", company_id=company.id)

        active = CompanyUser.create(
            user_id=user.id, company_id=company.id, role=UserRole.EMPLOYEE,
        )
        repo.save(active)

        results = repo.find_active_by_user_id(user.id)
        assert len(results) == 1

        # Deactivate and check
        active.deactivate()
        repo.save(active)
        results = repo.find_active_by_user_id(user.id)
        assert len(results) == 0

    def test_find_by_company_id(self, db_session, company, make_user):
        repo = CompanyUserRepository(db_session)
        user1 = make_user(email="emp1@testco.com", company_id=company.id)
        user2 = make_user(email="emp2@testco.com", company_id=company.id)

        repo.save(CompanyUser.create(user_id=user1.id, company_id=company.id))
        repo.save(CompanyUser.create(user_id=user2.id, company_id=company.id))

        results = repo.find_by_company_id(company.id)
        assert len(results) >= 2


class TestCompanyUserRepositoryCounts:
    def test_count_admins_in_company(self, db_session, company, make_user):
        repo = CompanyUserRepository(db_session)
        admin1 = make_user(email="a1@testco.com", role=UserRole.ADMIN, company_id=company.id)
        admin2 = make_user(email="a2@testco.com", role=UserRole.ADMIN, company_id=company.id)
        emp = make_user(email="e1@testco.com", role=UserRole.EMPLOYEE, company_id=company.id)

        repo.save(CompanyUser.create(user_id=admin1.id, company_id=company.id, role=UserRole.ADMIN))
        repo.save(CompanyUser.create(user_id=admin2.id, company_id=company.id, role=UserRole.ADMIN))
        repo.save(CompanyUser.create(user_id=emp.id, company_id=company.id, role=UserRole.EMPLOYEE))

        count = repo.count_admins_in_company(company.id)
        assert count == 2

    def test_count_active_memberships(self, db_session, company, make_user):
        repo = CompanyUserRepository(db_session)
        user = make_user(email="count-test@testco.com", company_id=company.id)

        active = CompanyUser.create(user_id=user.id, company_id=company.id)
        repo.save(active)

        assert repo.count_active_memberships(user.id) == 1

        active.deactivate()
        repo.save(active)
        assert repo.count_active_memberships(user.id) == 0


class TestCompanyUserRepositoryConstraints:
    def test_unique_constraint_on_user_company(self, db_session, company, make_user):
        repo = CompanyUserRepository(db_session)
        user = make_user(email="unique-test@testco.com", company_id=company.id)

        cu1 = CompanyUser.create(user_id=user.id, company_id=company.id)
        repo.save(cu1)

        cu2 = CompanyUser.create(user_id=user.id, company_id=company.id)
        with pytest.raises(IntegrityError):
            repo.save(cu2)
            db_session.flush()
