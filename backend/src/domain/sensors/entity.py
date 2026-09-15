from uuid import UUID


class Sensor:
    def __init__(
        self,
        id: UUID | None,
        device_type: str,
        display_name: str,
        default_config: dict,
    ):
        self.id = id
        self.device_type = device_type
        self.display_name = display_name
        self.default_config = default_config