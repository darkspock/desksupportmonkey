import pytest

from src.company_bc.department.domain.entities import Department


class TestDepartment:
    def test_create(self):
        dept = Department.create(company_id="comp123", name="Engineering")
        assert dept.name == "Engineering"
        assert dept.company_id == "comp123"
        assert dept.is_active is True
        assert len(dept.id) == 26

    def test_create_strips_name(self):
        dept = Department.create(company_id="comp123", name="  Sales  ")
        assert dept.name == "Sales"

    def test_create_empty_name_raises(self):
        with pytest.raises(ValueError, match="Department name is required"):
            Department.create(company_id="comp123", name="")

    def test_create_blank_name_raises(self):
        with pytest.raises(ValueError, match="Department name is required"):
            Department.create(company_id="comp123", name="   ")

    def test_deactivate(self):
        dept = Department.create(company_id="comp123", name="HR")
        assert dept.is_active is True
        dept.deactivate()
        assert dept.is_active is False

    def test_update_name(self):
        dept = Department.create(company_id="comp123", name="HR")
        dept.update_name("Human Resources")
        assert dept.name == "Human Resources"

    def test_update_name_strips(self):
        dept = Department.create(company_id="comp123", name="HR")
        dept.update_name("  Support  ")
        assert dept.name == "Support"

    def test_update_name_empty_raises(self):
        dept = Department.create(company_id="comp123", name="HR")
        with pytest.raises(ValueError, match="Department name is required"):
            dept.update_name("")
