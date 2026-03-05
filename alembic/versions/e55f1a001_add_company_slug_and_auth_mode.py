"""add company slug and auth_mode

Revision ID: e55f1a001
Revises: e9f0g1h2i3j4
Create Date: 2026-03-03 12:00:00.000000

"""
import re
import unicodedata
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e55f1a001"
down_revision: Union[str, None] = "e9f0g1h2i3j4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _generate_slug(name: str) -> str:
    """Generate URL-safe slug from company name (self-contained for migration)."""
    normalized = unicodedata.normalize("NFKD", name)
    ascii_name = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_name.lower()).strip("-")
    if len(slug) < 3:
        slug = slug + "-co"
    return slug[:50]


def upgrade() -> None:
    # Step 1: Add nullable slug and auth_mode columns
    op.add_column("companies", sa.Column("slug", sa.String(50), nullable=True))
    op.add_column(
        "companies",
        sa.Column("auth_mode", sa.String(20), nullable=False, server_default="domain"),
    )

    # Step 2: Generate slugs for existing companies
    conn = op.get_bind()
    companies = conn.execute(
        sa.text("SELECT id, name FROM companies ORDER BY created_at")
    ).fetchall()
    used_slugs: set[str] = set()
    for company_id, name in companies:
        base = _generate_slug(name)
        slug = base
        counter = 2
        while slug in used_slugs:
            slug = f"{base[:46]}-{counter}"
            counter += 1
        used_slugs.add(slug)
        conn.execute(
            sa.text("UPDATE companies SET slug = :slug WHERE id = :id"),
            {"slug": slug, "id": company_id},
        )

    # Step 3: Set NOT NULL and unique index
    op.alter_column("companies", "slug", nullable=False)
    op.create_unique_constraint("uq_companies_slug", "companies", ["slug"])
    op.create_index("ix_companies_slug", "companies", ["slug"])


def downgrade() -> None:
    op.drop_index("ix_companies_slug", table_name="companies")
    op.drop_constraint("uq_companies_slug", "companies", type_="unique")
    op.drop_column("companies", "auth_mode")
    op.drop_column("companies", "slug")
