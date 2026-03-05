"""create company_users table and add magic_links.company_id

Revision ID: e55f2a001
Revises: e55f1a001
Create Date: 2026-03-03 14:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

import ulid as ulid_lib

# revision identifiers, used by Alembic.
revision: str = "e55f2a001"
down_revision: Union[str, None] = "e55f1a001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Step 1: Create company_users table
    op.create_table(
        "company_users",
        sa.Column("id", sa.String(26), primary_key=True),
        sa.Column(
            "user_id",
            sa.String(26),
            sa.ForeignKey("users.id"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "company_id",
            sa.String(26),
            sa.ForeignKey("companies.id"),
            nullable=False,
            index=True,
        ),
        sa.Column("role", sa.String(30), nullable=False, server_default="employee"),
        sa.Column(
            "department_id",
            sa.String(26),
            sa.ForeignKey("departments.id"),
            nullable=True,
        ),
        sa.Column(
            "employee_role_id",
            sa.String(26),
            sa.ForeignKey("employee_roles.id"),
            nullable=True,
        ),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
        sa.UniqueConstraint(
            "user_id", "company_id", name="uq_company_users_user_company"
        ),
    )

    # Step 2: Populate company_users from existing users
    conn = op.get_bind()
    rows = conn.execute(
        sa.text(
            "SELECT id, company_id, role, department_id, employee_role_id, "
            "is_active, created_at, updated_at "
            "FROM users WHERE company_id IS NOT NULL"
        )
    ).fetchall()
    for row in rows:
        new_id = str(ulid_lib.new())
        conn.execute(
            sa.text(
                "INSERT INTO company_users "
                "(id, user_id, company_id, role, department_id, employee_role_id, "
                "is_active, created_at, updated_at) "
                "VALUES (:id, :user_id, :company_id, :role, :department_id, "
                ":employee_role_id, :is_active, :created_at, :updated_at)"
            ),
            {
                "id": new_id,
                "user_id": row[0],
                "company_id": row[1],
                "role": row[2],
                "department_id": row[3],
                "employee_role_id": row[4],
                "is_active": row[5],
                "created_at": row[6],
                "updated_at": row[7],
            },
        )

    # Step 3: Add company_id column to magic_links
    op.add_column("magic_links", sa.Column("company_id", sa.String(26), nullable=True))


def downgrade() -> None:
    op.drop_column("magic_links", "company_id")
    op.drop_table("company_users")
