import pytest

from domain.locations.config_builder import LocationConfigBuilder
from domain.locations.errors import ConfigurationError


def test_builder_creates_valid_location_config():
    config = (
        LocationConfigBuilder()
        .set_location_name("Greenhouse A")
        .add_zone(
            name="Zone 1",
            moisture_threshold_low=0.30,
            moisture_threshold_high=0.70,
            schedule={"watering": "08:00"},
        )
        .build()
    )

    assert config.location.name == "Greenhouse A"
    assert len(config.location.zones) == 1

    zone = config.location.zones[0]

    assert zone.name == "Zone 1"
    assert zone.moisture_threshold_low == 0.30
    assert zone.moisture_threshold_high == 0.70
    assert zone.schedule == {"watering": "08:00"}


def test_builder_rejects_missing_location_name():
    builder = LocationConfigBuilder()

    builder.add_zone(
        name="Zone 1",
        moisture_threshold_low=0.30,
        moisture_threshold_high=0.70,
    )

    with pytest.raises(ConfigurationError):
        builder.build()


def test_builder_rejects_no_zones():
    builder = LocationConfigBuilder()

    builder.set_location_name("Greenhouse A")

    with pytest.raises(ConfigurationError):
        builder.build()


def test_builder_rejects_invalid_threshold_order():
    builder = (
        LocationConfigBuilder()
        .set_location_name("Greenhouse A")
        .add_zone(
            name="Zone 1",
            moisture_threshold_low=0.80,
            moisture_threshold_high=0.40,
        )
    )

    with pytest.raises(ConfigurationError):
        builder.build()


def test_builder_rejects_threshold_outside_valid_range():
    builder = (
        LocationConfigBuilder()
        .set_location_name("Greenhouse A")
        .add_zone(
            name="Zone 1",
            moisture_threshold_low=-0.10,
            moisture_threshold_high=0.70,
        )
    )

    with pytest.raises(ConfigurationError):
        builder.build()


def test_builder_rejects_duplicate_zone_names():
    builder = (
        LocationConfigBuilder()
        .set_location_name("Greenhouse A")
        .add_zone(
            name="Zone 1",
            moisture_threshold_low=0.30,
            moisture_threshold_high=0.70,
        )
        .add_zone(
            name="Zone 1",
            moisture_threshold_low=0.40,
            moisture_threshold_high=0.80,
        )
    )

    with pytest.raises(ConfigurationError):
        builder.build()