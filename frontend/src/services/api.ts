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

export type DeviceDto = {
  id: string
  device_type: string
  role: 'sensor' | 'actuator'
  device_family: 'simulation' | 'edge'
  display_name: string
  default_config: Record<string, unknown>
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

export async function getDevices(
  family?: 'simulation' | 'edge',
  role?: 'sensor' | 'actuator',
): Promise<DeviceDto[]> {
  const params = new URLSearchParams()

  if (family) {
    params.set('family', family)
  }

  if (role) {
    params.set('role', role)
  }

  const query = params.toString()
  const url = query
    ? `${API_BASE_URL}/api/devices?${query}`
    : `${API_BASE_URL}/api/devices`

  const response = await fetch(url)

  if (!response.ok) {
    throw new Error('Failed to load devices')
  }

  return response.json()
}

export async function provisionDevices(
  family: 'simulation' | 'edge',
): Promise<DeviceDto[]> {
  const response = await fetch(
    `${API_BASE_URL}/api/devices/provision?family=${family}`,
    {
      method: 'POST',
    },
  )

  if (!response.ok) {
    const errorBody = await response.json().catch(() => null)

    throw new Error(
      errorBody?.detail || 'Failed to provision devices',
    )
  }

  return response.json()
}