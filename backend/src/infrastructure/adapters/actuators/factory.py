from domain.actuators.ports import ActuatorPort
from infrastructure.adapters.actuators.simulation import (
    SimulationActuatorAdapter,
)
from infrastructure.adapters.actuators.max_runtime_decorator import (
    MaxRunTimeActuatorDecorator,
)
from infrastructure.adapters.actuators.logging_decorator import (
    LoggingActuatorDecorator,
)
from infrastructure.persistence.device_repository import DeviceRepository
from infrastructure.persistence.execution_log_repository import (
    ExecutionLogRepository,
)


def build_actuator_port(
    device_repository: DeviceRepository,
    execution_log_repository: ExecutionLogRepository,
) -> ActuatorPort:
    """Build the actuator adapter with Phase 9 decorators."""

    simulation_adapter = SimulationActuatorAdapter()

    runtime_decorator = MaxRunTimeActuatorDecorator(
        wrapped=simulation_adapter,
        device_repository=device_repository,
    )

    logging_decorator = LoggingActuatorDecorator(
        wrapped=runtime_decorator,
        execution_log_repository=execution_log_repository,
    )

    return logging_decorator
