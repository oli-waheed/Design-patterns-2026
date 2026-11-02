
export type ActuatorState =
  | 'off'
  | 'idle'
  | 'running'
  | 'error'
  | 'maintenance'

export type ActuatorStateDto = {
  device_id: string
  state: ActuatorState
  allowed_commands: string[]
}

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export async function getActuatorState(
  deviceId: string,
): Promise<ActuatorStateDto> {
  const response = await fetch(
    `${API_BASE_URL}/api/devices/${deviceId}/state`,
  )

  if (!response.ok) {
    const errorBody = await response.json().catch(() => null)

    throw new Error(
      errorBody?.detail || 'Failed to load actuator state',
    )
  }

  return response.json()
}
