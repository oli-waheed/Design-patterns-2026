"""schema hardening

Phase 12. Forward-only hardening of the schema that grew in Phases 2-11:

- indexes for the live dashboard queries (alerts, command and execution
  history, devices by location)
- zone thresholds stored as NUMERIC(5, 4), matching the ORM model
- CHECK constraints for status and severity values the app already uses
- an idempotent demo seed so the dashboard moves without hardware

Foreign-key ON DELETE behaviour was already set in earlier revisions and is
documented in docs/schema.md.

Revision ID: 8cc04ca37e07
Revises: 4ca2aa600344
Create Date: 2026-11-22

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "8cc04ca37e07"
down_revision: Union[str, Sequence[str], None] = "4ca2aa600344"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Fixed ids keep the seed idempotent: re-running it inserts nothing new.
DEMO_LOCATION_ID = "00000000-0000-4000-8000-000000000001"
DEMO_ZONE_ID = "00000000-0000-4000-8000-000000000002"
DEMO_SENSOR_ID = "00000000-0000-4000-8000-000000000003"
DEMO_PUMP_ID = "00000000-0000-4000-8000-000000000004"
DEMO_READING_ID = "00000000-0000-4000-8000-000000000005"


def seed_demo_data() -> None:
    """Insert demo rows only when they do not exist yet."""

    op.execute(
        f"""
        INSERT INTO locations (id, name)
        VALUES ('{DEMO_LOCATION_ID}', 'Demo Greenhouse')
        ON CONFLICT (id) DO NOTHING
        """
    )

    op.execute(
        f"""
        INSERT INTO zones (
            id, location_id, name,
            moisture_threshold_low, moisture_threshold_high, schedule
        )
        VALUES (
            '{DEMO_ZONE_ID}', '{DEMO_LOCATION_ID}', 'Bench 1',
            0.20, 0.60, '{{}}'::jsonb
        )
        ON CONFLICT (id) DO NOTHING
        """
    )

    # Simulation moisture sensor sampled every 5 seconds with tracking on,
    # assigned to Bench 1 so the zone view moves with no hardware.
    op.execute(
        f"""
        INSERT INTO devices (
            id, device_type, role, device_family, display_name,
            default_config, zone_id, location_id,
            sampling_interval_seconds, tracking_enabled
        )
        VALUES (
            '{DEMO_SENSOR_ID}', 'moisture_sensor', 'sensor', 'simulation',
            'Demo Moisture Sensor',
            '{{"unit": "vwc", "protocol": "simulation", "threshold": 0.2}}'::jsonb,
            '{DEMO_ZONE_ID}', '{DEMO_LOCATION_ID}',
            5, true
        )
        ON CONFLICT (id) DO NOTHING
        """
    )

    # Unassigned simulation pump (no location or zone).
    op.execute(
        f"""
        INSERT INTO devices (
            id, device_type, role, device_family, display_name,
            default_config, sampling_interval_seconds, tracking_enabled
        )
        VALUES (
            '{DEMO_PUMP_ID}', 'water_pump', 'actuator', 'simulation',
            'Demo Water Pump',
            '{{"protocol": "simulation", "default_state": "off"}}'::jsonb,
            300, true
        )
        ON CONFLICT (id) DO NOTHING
        """
    )

    op.execute(
        f"""
        INSERT INTO actuator_states (device_id, state)
        VALUES ('{DEMO_PUMP_ID}', 'idle')
        ON CONFLICT (device_id) DO NOTHING
        """
    )

    op.execute(
        f"""
        INSERT INTO sensor_readings (
            id, device_id, value, unit, source, recorded_at
        )
        VALUES (
            '{DEMO_READING_ID}', '{DEMO_SENSOR_ID}', 0.42, 'vwc',
            'simulation', now()
        )
        ON CONFLICT (id) DO NOTHING
        """
    )


def upgrade() -> None:
    """Apply indexes, type alignment, checks, and the demo seed."""

    op.create_index(
        "ix_alerts_location_created_at",
        "alerts",
        ["location_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_alerts_status_created_at",
        "alerts",
        ["status", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_command_log_created_at",
        "command_log",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        "ix_actuator_execution_log_created_at",
        "actuator_execution_log",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        "ix_devices_location_id",
        "devices",
        ["location_id"],
        unique=False,
    )

    op.alter_column(
        "zones",
        "moisture_threshold_low",
        existing_type=sa.DOUBLE_PRECISION(precision=53),
        type_=sa.Numeric(precision=5, scale=4),
        existing_nullable=False,
    )
    op.alter_column(
        "zones",
        "moisture_threshold_high",
        existing_type=sa.DOUBLE_PRECISION(precision=53),
        type_=sa.Numeric(precision=5, scale=4),
        existing_nullable=False,
    )

    op.create_check_constraint(
        "ck_alerts_severity",
        "alerts",
        "severity IN ('info', 'warning', 'critical')",
    )
    op.create_check_constraint(
        "ck_alerts_status",
        "alerts",
        "status IN ('active', 'resolved')",
    )
    op.create_check_constraint(
        "ck_command_log_status",
        "command_log",
        "status IN ('success', 'failed', 'rejected')",
    )

    seed_demo_data()


def downgrade() -> None:
    """Remove the hardening changes. Seed rows are left in place."""

    op.drop_constraint("ck_command_log_status", "command_log", type_="check")
    op.drop_constraint("ck_alerts_status", "alerts", type_="check")
    op.drop_constraint("ck_alerts_severity", "alerts", type_="check")

    op.alter_column(
        "zones",
        "moisture_threshold_high",
        existing_type=sa.Numeric(precision=5, scale=4),
        type_=sa.DOUBLE_PRECISION(precision=53),
        existing_nullable=False,
    )
    op.alter_column(
        "zones",
        "moisture_threshold_low",
        existing_type=sa.Numeric(precision=5, scale=4),
        type_=sa.DOUBLE_PRECISION(precision=53),
        existing_nullable=False,
    )

    op.drop_index("ix_devices_location_id", table_name="devices")
    op.drop_index(
        "ix_actuator_execution_log_created_at",
        table_name="actuator_execution_log",
    )
    op.drop_index("ix_command_log_created_at", table_name="command_log")
    op.drop_index("ix_alerts_status_created_at", table_name="alerts")
    op.drop_index("ix_alerts_location_created_at", table_name="alerts")
