
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
  zone_id?: string | null
  location_id?: string | null
  sampling_interval_seconds: number
  tracking_enabled: boolean
}

export type SamplingUpdateRequest = {
  sampling_interval_seconds: number
  tracking_enabled: boolean
}

export type SamplingResponse = {
  device_id: string
  sampling_interval_seconds: number
  tracking_enabled: boolean
}

export type ZoneDto = {
  id: string
  location_id: string
  name: string
  moisture_threshold_low: number
  moisture_threshold_high: number
  schedule: Record<string, unknown>
}

export type LocationSummaryDto = {
  id: string
  name: string
}

export type LocationResponseDto = {
  location: LocationSummaryDto
  zones: ZoneDto[]
}

export type ZoneInput = {
  name: string
  moisture_threshold_low: number
  moisture_threshold_high: number
  schedule?: Record<string, unknown>
}

export type CreateLocationRequest = {
  location_name: string
  zones: ZoneInput[]
}

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

async function getErrorMessage(
  response: Response,
  fallback: string,
): Promise<string> {
  const errorBody = await response.json().catch(() => null)

  return errorBody?.detail || fallback
}

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
    throw new Error(
      await getErrorMessage(
        response,
        'Failed to create sensor',
      ),
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
    throw new Error(
      await getErrorMessage(
        response,
        'Failed to provision devices',
      ),
    )
  }

  return response.json()
}

export async function updateDeviceSampling(
  deviceId: string,
  request: SamplingUpdateRequest,
): Promise<SamplingResponse> {
  const response = await fetch(
    `${API_BASE_URL}/api/devices/${deviceId}/sampling`,
    {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    },
  )

  if (!response.ok) {
    throw new Error(
      await getErrorMessage(
        response,
        'Failed to update sampling settings',
      ),
    )
  }

  return response.json()
}

/* ---------------- Locations ---------------- */

export async function getLocations(): Promise<
  LocationSummaryDto[]
> {
  const response = await fetch(
    `${API_BASE_URL}/api/locations`,
  )

  if (!response.ok) {
    throw new Error(
      await getErrorMessage(
        response,
        'Failed to load locations',
      ),
    )
  }

  return response.json()
}

export async function getLocation(
  locationId: string,
): Promise<LocationResponseDto> {
  const response = await fetch(
    `${API_BASE_URL}/api/locations/${locationId}`,
  )

  if (!response.ok) {
    throw new Error(
      await getErrorMessage(
        response,
        'Failed to load location',
      ),
    )
  }

  return response.json()
}

export async function createLocation(
  request: CreateLocationRequest,
): Promise<LocationResponseDto> {
  const response = await fetch(
    `${API_BASE_URL}/api/locations`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    },
  )

  if (!response.ok) {
    throw new Error(
      await getErrorMessage(
        response,
        'Failed to create location',
      ),
    )
  }

  return response.json()
}

export async function deleteLocation(
  locationId: string,
): Promise<void> {
  const response = await fetch(
    `${API_BASE_URL}/api/locations/${locationId}`,
    {
      method: 'DELETE',
    },
  )

  if (!response.ok) {
    throw new Error(
      await getErrorMessage(
        response,
        'Failed to delete location',
      ),
    )
  }
}

/* ---------------- Zones ---------------- */

export async function addZone(
  locationId: string,
  zone: ZoneInput,
): Promise<ZoneDto> {
  const response = await fetch(
    `${API_BASE_URL}/api/locations/${locationId}/zones`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(zone),
    },
  )

  if (!response.ok) {
    throw new Error(
      await getErrorMessage(
        response,
        'Failed to add zone',
      ),
    )
  }

  return response.json()
}

export async function updateZone(
  locationId: string,
  zoneId: string,
  zone: ZoneInput,
): Promise<ZoneDto> {
  const response = await fetch(
    `${API_BASE_URL}/api/locations/${locationId}/zones/${zoneId}`,
    {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(zone),
    },
  )

  if (!response.ok) {
    throw new Error(
      await getErrorMessage(
        response,
        'Failed to update zone',
      ),
    )
  }

  return response.json()
}

export async function deleteZone(
  locationId: string,
  zoneId: string,
): Promise<void> {
  const response = await fetch(
    `${API_BASE_URL}/api/locations/${locationId}/zones/${zoneId}`,
    {
      method: 'DELETE',
    },
  )

  if (!response.ok) {
    throw new Error(
      await getErrorMessage(
        response,
        'Failed to delete zone',
      ),
    )
  }
}

/* ---------------- Device assignment ---------------- */

export async function assignDeviceToZone(
  deviceId: string,
  zoneId: string | null,
): Promise<void> {
  const response = await fetch(
    `${API_BASE_URL}/api/devices/${deviceId}/zone`,
    {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        zone_id: zoneId,
      }),
    },
  )

  if (!response.ok) {
    throw new Error(
      await getErrorMessage(
        response,
        'Failed to assign device',
      ),
    )
  }
}

export async function getZoneDevices(
  locationId: string,
  zoneId: string,
): Promise<DeviceDto[]> {
  const response = await fetch(
    `${API_BASE_URL}/api/locations/${locationId}/zones/${zoneId}/devices`,
  )

  if (!response.ok) {
    throw new Error(
      await getErrorMessage(
        response,
        'Failed to load zone devices',
      ),
    )
  }

  return response.json()
}

/* ---------------- Automation Strategy (Phase 6) ---------------- */

export type StrategyKey = 'conservative' | 'aggressive'

export type StrategySelectionRequest = {
  strategy_key: StrategyKey
}

export type ZoneRecommendationDto = {
  zone_id: string
  zone_name: string
  moisture: number | null
  low_threshold: number
  high_threshold: number
  action: string
  reason: string
  score?: number | null
}

export type AutomationEvaluationDto = {
  location_id: string
  strategy_key: StrategyKey
  recommendations: ZoneRecommendationDto[]
}

export async function saveAutomationStrategy(
  locationId: string,
  strategyKey: StrategyKey,
): Promise<{ location_id: string; strategy_key: StrategyKey }> {
  const response = await fetch(
    `${API_BASE_URL}/api/locations/${locationId}/automation/strategy`,
    {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        strategy_key: strategyKey,
      } satisfies StrategySelectionRequest),
    },
  )

  if (!response.ok) {
    throw new Error(
      await getErrorMessage(
        response,
        'Failed to save automation strategy',
      ),
    )
  }

  return response.json()
}

export async function evaluateAutomation(
  locationId: string,
): Promise<AutomationEvaluationDto> {
  const response = await fetch(
    `${API_BASE_URL}/api/locations/${locationId}/automation/evaluate`,
    {
      method: 'POST',
    },
  )

  if (!response.ok) {
    throw new Error(
      await getErrorMessage(
        response,
        'Failed to evaluate automation',
      ),
    )
  }

  return response.json()
}
