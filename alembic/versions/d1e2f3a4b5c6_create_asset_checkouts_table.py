"""create asset_checkouts table and add source_type to maintenance_records

Revision ID: d1e2f3a4b5c6
Revises: c7d8e9f0a1b2
Create Date: 2026-02-26
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


revision = "d1e2f3a4b5c6"
down_revision = "c7d8e9f0a1b2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- 1. Create asset_checkouts table ---
    op.create_table(
        "asset_checkouts",
        sa.Column("id", sa.String(26), nullable=False),
        sa.Column("company_id", sa.String(26), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("asset_id", sa.String(26), sa.ForeignKey("assets.id"), nullable=False),
        sa.Column("user_id", sa.String(26), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("checked_out_by", sa.String(26), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("checked_out_at", sa.DateTime(), nullable=False),
        sa.Column("condition_out", sa.String(20), nullable=False),
        sa.Column("condition_out_notes", sa.Text(), nullable=True),
        sa.Column("notes_out", sa.Text(), nullable=True),
        sa.Column("accepted_at", sa.DateTime(), nullable=True),
        sa.Column("checked_in_at", sa.DateTime(), nullable=True),
        sa.Column("checked_in_by", sa.String(26), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("condition_in", sa.String(20), nullable=True),
        sa.Column("condition_in_notes", sa.Text(), nullable=True),
        sa.Column("notes_in", sa.Text(), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(), nullable=True),
        sa.Column("cancelled_by", sa.String(26), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("cancel_reason", sa.Text(), nullable=True),
        sa.Column("maintenance_id", sa.String(26), nullable=True),
        sa.Column("auto_assigned", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_asset_checkouts_company_id", "asset_checkouts", ["company_id"])
    op.create_index("ix_asset_checkouts_asset_id", "asset_checkouts", ["asset_id"])
    op.create_index("ix_asset_checkouts_user_id", "asset_checkouts", ["user_id"])
    op.create_index(
        "uq_asset_checkouts_active",
        "asset_checkouts",
        ["asset_id"],
        unique=True,
        postgresql_where=text("checked_in_at IS NULL AND cancelled_at IS NULL"),
    )

    # --- 2. Add source_type to maintenance_records ---
    op.add_column(
        "maintenance_records",
        sa.Column("source_type", sa.String(30), nullable=True),
    )

    # --- 3. Remove EMPLOYEE system locations ---
    # Move assets at EMPLOYEE locations to location_id = NULL
    conn = op.get_bind()
    conn.execute(
        text("""
            UPDATE assets
            SET location_id = NULL
            WHERE location_id IN (
                SELECT id FROM asset_locations
                WHERE is_system = true AND system_key = 'employee'
            )
        """)
    )
    # Delete the EMPLOYEE system locations
    conn.execute(
        text("DELETE FROM asset_locations WHERE is_system = true AND system_key = 'employee'")
    )

    # --- 4. Seed GDPR sanitization maintenance template per company ---
    import ulid as _ulid

    companies = conn.execute(text("SELECT id FROM companies")).fetchall()
    for (company_id,) in companies:
        # Check if template already exists
        existing = conn.execute(
            text(
                "SELECT id FROM maintenance_templates WHERE company_id = :cid AND name = 'GDPR Sanitization'"
            ),
            {"cid": company_id},
        ).fetchone()
        if existing:
            continue
        template_id = str(_ulid.new())
        conn.execute(
            text("""
                INSERT INTO maintenance_templates (id, company_id, name, default_priority, description, is_active, created_at)
                VALUES (:id, :cid, 'GDPR Sanitization', 'HIGH', 'GDPR data sanitization before asset reassignment', true, now())
            """),
            {"id": template_id, "cid": company_id},
        )
        checklist_titles = [
            "Factory reset / disk wipe",
            "Remove MDM/enrollment profile",
            "Deauthorize software licenses",
            "Remove from employee account",
            "Verify no personal data remains",
            "Compliance sign-off",
        ]
        for i, title in enumerate(checklist_titles):
            item_id = str(_ulid.new())
            conn.execute(
                text("""
                    INSERT INTO maintenance_checklist_items (id, template_id, title, is_required, sort_order)
                    VALUES (:id, :tid, :title, true, :pos)
                """),
                {"id": item_id, "tid": template_id, "title": title, "pos": i},
            )


def downgrade() -> None:
    op.drop_column("maintenance_records", "source_type")
    op.drop_index("uq_asset_checkouts_active", table_name="asset_checkouts")
    op.drop_index("ix_asset_checkouts_user_id", table_name="asset_checkouts")
    op.drop_index("ix_asset_checkouts_asset_id", table_name="asset_checkouts")
    op.drop_index("ix_asset_checkouts_company_id", table_name="asset_checkouts")
    op.drop_table("asset_checkouts")
