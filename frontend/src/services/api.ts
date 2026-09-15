export type HealthResponse = {
  status: 'ok' | 'degraded'
  db: 'ok' | 'fail'
}

export type Sensor = {
  id: string
  device_type: string
  display_name: string
  default_config: Record<string, unknown>
}

export type CreateSensorRequest = {
  type: 'moisture' | 'light'
  display_name?: string
}

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export async function getHealth(): Promise<HealthResponse> {
  const response = await fetch(`${API_BASE_URL}/health`)

  if (!response.ok) {
    throw new Error('Health check failed')
  }

  return response.json()
}

export async function getSensors(): Promise<Sensor[]> {
  const response = await fetch(`${API_BASE_URL}/api/sensors`)

  if (!response.ok) {
    throw new Error('Failed to load sensors')
  }

  return response.json()
}

export async function createSensor(
  request: CreateSensorRequest,
): Promise<Sensor> {
  const response = await fetch(`${API_BASE_URL}/api/sensors`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  })

  if (!response.ok) {
    const errorBody = await response.json().catch(() => null)

    throw new Error(
      errorBody?.detail || 'Failed to create sensor',
    )
  }

  return response.json()
}