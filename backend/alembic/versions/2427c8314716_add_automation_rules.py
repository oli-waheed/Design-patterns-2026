
"""Add automation rules.

Revision ID: 2427c8314716
Revises: d57d17a10ef2
Create Date: 2026-10-13
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# Revision identifiers used by Alembic.
revision: str = "2427c8314716"
down_revision: Union[str, Sequence[str], None] = "d57d17a10ef2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create the automation rules table."""

    op.create_table(
        "automation_rules",
        sa.Column(
            "id",
            sa.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "location_id",
            sa.UUID(),
            nullable=False,
        ),
        sa.Column(
            "strategy_key",
            sa.String(length=32),
            server_default=sa.text("'conservative'"),
            nullable=False,
        ),
        sa.Column(
            "parameters",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["location_id"],
            ["locations.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "location_id",
            name="uq_automation_rules_location_id",
        ),
    )


def downgrade() -> None:
    """Remove the automation rules table."""

    op.drop_table("automation_rules")
