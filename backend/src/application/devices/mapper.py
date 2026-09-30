from domain.devices.entity import Device

from application.devices.dto import DeviceDto


class DeviceMapper:
    @staticmethod
    def to_dto(device: Device) -> DeviceDto:
        return DeviceDto(
            id=device.id,
            device_type=device.device_type,
            role=device.role,
            device_family=device.device_family,
            display_name=device.display_name,
            default_config=device.default_config,
            zone_id=device.zone_id,
            location_id=device.location_id,
        )

    @staticmethod
    def to_domain(dto: DeviceDto) -> Device:
        return Device(
            id=dto.id,
            device_type=dto.device_type,
            role=dto.role,
            device_family=dto.device_family,
            display_name=dto.display_name,
            default_config=dto.default_config,
            zone_id=dto.zone_id,
            location_id=dto.location_id,
        )