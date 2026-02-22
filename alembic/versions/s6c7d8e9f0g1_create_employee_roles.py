"""create employee_roles table and add employee_role_id to users and equipment_profiles

Revision ID: s6c7d8e9f0g1
Revises: r5b6c7d8e9f0
Create Date: 2026-02-22 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision = "s6c7d8e9f0g1"
down_revision = "r5b6c7d8e9f0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "employee_roles",
        sa.Column("id", sa.String(26), primary_key=True),
        sa.Column("company_id", sa.String(26), sa.ForeignKey("companies.id"), nullable=False, index=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("company_id", "name", name="uq_employee_role_company_name"),
    )

    # Add employee_role_id to users
    op.add_column(
        "users",
        sa.Column("employee_role_id", sa.String(26), nullable=True),
    )
    op.create_foreign_key(
        "fk_users_employee_role_id",
        "users",
        "employee_roles",
        ["employee_role_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_users_employee_role_id", "users", ["employee_role_id"])

    # Replace equipment_profiles.role with employee_role_id
    op.add_column(
        "equipment_profiles",
        sa.Column("employee_role_id", sa.String(26), nullable=True),
    )
    op.create_foreign_key(
        "fk_equipment_profiles_employee_role_id",
        "equipment_profiles",
        "employee_roles",
        ["employee_role_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_equipment_profiles_employee_role_id", "equipment_profiles", ["employee_role_id"])

    # Drop old unique index on role and create new one on employee_role_id
    op.drop_index("ix_equipment_profile_active_unique", table_name="equipment_profiles")
    op.create_index(
        "ix_equipment_profile_active_unique",
        "equipment_profiles",
        ["company_id", "department_id", "employee_role_id"],
        unique=True,
        postgresql_where=sa.text("is_active = true"),
    )

    op.drop_column("equipment_profiles", "role")


def downgrade() -> None:
    op.add_column(
        "equipment_profiles",
        sa.Column("role", sa.String(20), nullable=True),
    )

    op.drop_index("ix_equipment_profile_active_unique", table_name="equipment_profiles")
    op.create_index(
        "ix_equipment_profile_active_unique",
        "equipment_profiles",
        ["company_id", "department_id", "role"],
        unique=True,
        postgresql_where=sa.text("is_active = true"),
    )

    op.drop_index("ix_equipment_profiles_employee_role_id", table_name="equipment_profiles")
    op.drop_constraint("fk_equipment_profiles_employee_role_id", "equipment_profiles", type_="foreignkey")
    op.drop_column("equipment_profiles", "employee_role_id")

    op.drop_index("ix_users_employee_role_id", table_name="users")
    op.drop_constraint("fk_users_employee_role_id", "users", type_="foreignkey")
    op.drop_column("users", "employee_role_id")

    op.drop_table("employee_roles")
