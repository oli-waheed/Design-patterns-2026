from uuid import UUID

from domain.devices.entity import Device
from domain.devices.family_factory import get_family_factory
from infrastructure.persistence.device_repository import DeviceRepository


class DevicesService:
    def __init__(
        self,
        repository: DeviceRepository,
    ):
        self._repository = repository

    def provision_family(
        self,
        family: str,
    ) -> list[Device]:
        factory = get_family_factory(family)

        devices = factory.create_device_set()

        return self._repository.save_devices(devices)

    def list_devices(
        self,
        device_family: str | None = None,
        role: str | None = None,
    ) -> list[Device]:
        return self._repository.list_devices(
            device_family=device_family,
            role=role,
        )

    def assign_zone(
        self,
        device_id: UUID,
        zone_id: UUID | None,
    ) -> bool:
        return self._repository.assign_zone(
            device_id=device_id,
            zone_id=zone_id,
        )

    def list_devices_in_zone(
        self,
        location_id: UUID,
        zone_id: UUID,
    ) -> list[Device]:
        return self._repository.list_devices_in_zone(
            location_id=location_id,
            zone_id=zone_id,
        )