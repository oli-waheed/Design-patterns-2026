"""Adapter (Phase 5) and ingest through HTTP into sensor_readings."""

from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from infrastructure.persistence.models import ReadingRow

from .seed_ids import DEMO_SENSOR_ID


def rows_for(db, device_id):
    return db.scalars(
        select(ReadingRow)
        .where(ReadingRow.device_id == device_id)
        .order_by(ReadingRow.recorded_at)
    ).all()


def test_take_a_reading_stores_a_simulation_row(client, db):
    before = len(rows_for(db, DEMO_SENSOR_ID))

    response = client.post(f"/api/sensors/{DEMO_SENSOR_ID}/read")

    assert response.status_code == 200
    rows = rows_for(db, DEMO_SENSOR_ID)
    assert len(rows) == before + 1
    assert rows[-1].source == "simulation"
    assert float(rows[-1].value) == response.json()["value"]


def test_device_http_reading_is_stored_with_http_source(client, db):
    response = client.post(
        f"/api/devices/{DEMO_SENSOR_ID}/readings",
        json={"value": 0.41, "unit": "vwc"},
    )

    assert response.status_code == 201
    latest = rows_for(db, DEMO_SENSOR_ID)[-1]
    assert (float(latest.value), latest.unit, latest.source) == (0.41, "vwc", "http")


def test_range_query_returns_exactly_the_rows_in_the_window(client, db):
    for value in (0.31, 0.32, 0.33):
        client.post(
            f"/api/devices/{DEMO_SENSOR_ID}/readings",
            json={"value": value, "unit": "vwc"},
        )

    now = datetime.now(timezone.utc)
    response = client.get(
        f"/api/sensors/{DEMO_SENSOR_ID}/readings",
        params={
            "from": (now - timedelta(minutes=5)).isoformat(),
            "to": (now + timedelta(minutes=1)).isoformat(),
        },
    )

    in_window = [
        float(row.value)
        for row in rows_for(db, DEMO_SENSOR_ID)
        if row.recorded_at >= now - timedelta(minutes=5)
    ]

    assert [row["value"] for row in response.json()] == in_window
    assert in_window[-3:] == [0.31, 0.32, 0.33]
