
"""Add persistent actuator states.

Revision ID: 5a8c2f1d9e30
Revises: 2427c8314716
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# Revision identifiers used by Alembic.
revision: str = "5a8c2f1d9e30"
down_revision: Union[str, Sequence[str], None] = "2427c8314716"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create actuator states and initialise existing actuators."""

    op.create_table(
        "actuator_states",
        sa.Column(
            "device_id",
            sa.UUID(),
            nullable=False,
        ),
        sa.Column(
            "state",
            sa.String(length=32),
            server_default=sa.text("'idle'"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["device_id"],
            ["devices.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("device_id"),
    )

    # Give existing actuator devices an initial idle state.
    op.execute(
        """
        INSERT INTO actuator_states (device_id, state)
        SELECT id, 'idle'
        FROM devices
        WHERE role = 'actuator'
        """
    )


def downgrade() -> None:
    """Remove the actuator states table."""

    op.drop_table("actuator_states")
