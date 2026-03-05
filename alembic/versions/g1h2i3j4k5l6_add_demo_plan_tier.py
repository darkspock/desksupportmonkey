"""add demo plan tier - data migration

Revision ID: g1h2i3j4k5l6
Revises: f0a1b2c3d4e5
Create Date: 2026-03-05 10:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "g1h2i3j4k5l6"
down_revision: Union[str, None] = "f0a1b2c3d4e5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Set plan='demo' and copy demo_expires_at to trial_ends_at for companies
    linked to ResellerClient with is_demo=True.

    No schema changes needed — plan is String(20), 'demo' fits.
    """
    conn = op.get_bind()

    # Find companies linked to demo reseller clients
    result = conn.execute(
        sa.text(
            """
            UPDATE companies
            SET plan = 'demo',
                trial_ends_at = COALESCE(
                    (SELECT rc.demo_expires_at
                     FROM reseller_clients rc
                     WHERE rc.company_id = companies.id AND rc.is_demo = true
                     LIMIT 1),
                    trial_ends_at
                )
            WHERE id IN (
                SELECT company_id FROM reseller_clients WHERE is_demo = true
            )
            AND plan != 'demo'
            """
        )
    )
    updated = result.rowcount
    if updated:
        print(f"  Migrated {updated} demo companies to plan='demo'")


def downgrade() -> None:
    """Revert demo companies back to free plan."""
    conn = op.get_bind()
    conn.execute(
        sa.text("UPDATE companies SET plan = 'free' WHERE plan = 'demo'")
    )
