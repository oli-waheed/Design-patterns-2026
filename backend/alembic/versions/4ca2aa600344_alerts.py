"""alerts

Revision ID: 4ca2aa600344
Revises: ab97c0ab7037
Create Date: 2026-11-22

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "4ca2aa600344"
down_revision: Union[str, Sequence[str], None] = "ab97c0ab7037"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create the alerts table written by the alert subscriber."""

    op.create_table(
        "alerts",
        sa.Column(
            "id",
            sa.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("location_id", sa.UUID(), nullable=True),
        sa.Column("zone_id", sa.UUID(), nullable=True),
        sa.Column("device_id", sa.UUID(), nullable=True),
        sa.Column("severity", sa.String(length=16), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column(
            "status",
            sa.String(length=16),
            server_default=sa.text("'active'"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "acknowledged_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["location_id"],
            ["locations.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["zone_id"],
            ["zones.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["device_id"],
            ["devices.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        op.f("ix_alerts_created_at"),
        "alerts",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_alerts_location_id"),
        "alerts",
        ["location_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_alerts_zone_id"),
        "alerts",
        ["zone_id"],
        unique=False,
    )


def downgrade() -> None:
    """Remove the alerts table."""

    op.drop_index(op.f("ix_alerts_zone_id"), table_name="alerts")
    op.drop_index(op.f("ix_alerts_location_id"), table_name="alerts")
    op.drop_index(op.f("ix_alerts_created_at"), table_name="alerts")
    op.drop_table("alerts")
