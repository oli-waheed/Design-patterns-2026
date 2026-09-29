from typing import Any

from domain.locations.entity import Location, LocationConfig, Zone
from domain.locations.errors import ConfigurationError


class LocationConfigBuilder:
    def __init__(self) -> None:
        self._location_name: str | None = None
        self._zones: list[Zone] = []

    def set_location_name(self, name: str) -> "LocationConfigBuilder":
        self._location_name = name
        return self

    def add_zone(
        self,
        name: str,
        moisture_threshold_low: float,
        moisture_threshold_high: float,
        schedule: dict[str, Any] | None = None,
    ) -> "LocationConfigBuilder":
        zone = Zone(
            name=name,
            moisture_threshold_low=moisture_threshold_low,
            moisture_threshold_high=moisture_threshold_high,
            schedule=schedule or {},
        )

        self._zones.append(zone)

        return self

    def build(self) -> LocationConfig:
        self._validate_location_name()
        self._validate_zones()

        location = Location(
            name=self._location_name.strip(),
            zones=tuple(self._zones),
        )

        return LocationConfig(location=location)

    def _validate_location_name(self) -> None:
        if self._location_name is None:
            raise ConfigurationError(
                "Location name is required."
            )

        if not self._location_name.strip():
            raise ConfigurationError(
                "Location name must not be empty."
            )

    def _validate_zones(self) -> None:
        if not self._zones:
            raise ConfigurationError(
                "At least one zone is required."
            )

        zone_names: set[str] = set()

        for zone in self._zones:
            name = zone.name.strip()

            if not name:
                raise ConfigurationError(
                    "Zone name must not be empty."
                )

            normalized_name = name.casefold()

            if normalized_name in zone_names:
                raise ConfigurationError(
                    f"Zone name must be unique: {zone.name}"
                )

            zone_names.add(normalized_name)

            low = zone.moisture_threshold_low
            high = zone.moisture_threshold_high

            if not 0.0 <= low <= 1.0:
                raise ConfigurationError(
                    "Low moisture threshold must be between 0.0 and 1.0."
                )

            if not 0.0 <= high <= 1.0:
                raise ConfigurationError(
                    "High moisture threshold must be between 0.0 and 1.0."
                )

            if low >= high:
                raise ConfigurationError(
                    "Low moisture threshold must be less than high threshold."
                )