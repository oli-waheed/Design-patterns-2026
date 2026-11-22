import { API_BASE_URL } from './api'

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

export type ActuatorExecutionDto = {
  id: string
  device_id: string
  device_name: string
  success: boolean
  policy_applied: string[]
  message: string | null
  created_at: string
}


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

export async function getActuatorExecutions(
  limit = 20,
): Promise<ActuatorExecutionDto[]> {
  const response = await fetch(
    `${API_BASE_URL}/api/actuators/executions?limit=${limit}`,
  )

  if (!response.ok) {
    const errorBody = await response.json().catch(() => null)

    throw new Error(
      errorBody?.detail || 'Failed to load actuator execution history',
    )
  }

  return response.json()
}

/* ---------------- Command Pattern (Phase 10) ---------------- */

export type CommandStatus = 'success' | 'failed' | 'rejected'

export type CommandLogDto = {
  id: string
  device_id: string
  command_type: string
  payload: Record<string, unknown>
  status: CommandStatus
  error_message: string | null
  created_at: string
}

export type ExecuteCommandRequest = {
  device_id: string
  command_type: string
  payload?: Record<string, unknown>
}

export async function executeCommand(
  request: ExecuteCommandRequest,
): Promise<CommandLogDto> {
  const response = await fetch(`${API_BASE_URL}/api/commands`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  })

  const result = await response.json().catch(() => null)

  // HTTP 409 contains a valid command-log record for rejected commands.
  if (!response.ok && response.status !== 409) {
    throw new Error(
      result?.detail || 'Failed to execute command',
    )
  }

  if (!result) {
    throw new Error('The server returned an invalid command response.')
  }

  return result as CommandLogDto
}

export async function getCommandHistory(
  limit = 50,
): Promise<CommandLogDto[]> {
  const response = await fetch(
    `${API_BASE_URL}/api/commands?limit=${limit}`,
  )

  if (!response.ok) {
    const errorBody = await response.json().catch(() => null)

    throw new Error(
      errorBody?.detail || 'Failed to load command history',
    )
  }

  return response.json()
}
