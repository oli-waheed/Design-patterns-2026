import type { DeviceDto } from '../../services/api'

type DeviceFamily = 'simulation' | 'edge'

type DeviceFamilySwitcherProps = {
  family: DeviceFamily
  onFamilyChange: (family: DeviceFamily) => void
  devices: DeviceDto[]
}

export default function DeviceFamilySwitcher({
  family,
  onFamilyChange,
  devices,
}: DeviceFamilySwitcherProps) {
  return (
    <div className="rounded-lg border bg-gray-50 p-4">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h4 className="font-semibold">Device family</h4>

          <p className="mt-1 text-sm text-gray-500">
            Choose which device family to manage.
          </p>
        </div>

        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => onFamilyChange('simulation')}
            className={`rounded-md px-4 py-2 text-sm font-medium ${
              family === 'simulation'
                ? 'bg-gray-900 text-white'
                : 'border bg-white text-gray-700'
            }`}
          >
            Simulation
          </button>

          <button
            type="button"
            onClick={() => onFamilyChange('edge')}
            className={`rounded-md px-4 py-2 text-sm font-medium ${
              family === 'edge'
                ? 'bg-gray-900 text-white'
                : 'border bg-white text-gray-700'
            }`}
          >
            Edge
          </button>
        </div>
      </div>

      <p className="mt-4 text-sm text-gray-600">
        {devices.length} device
        {devices.length === 1 ? '' : 's'} currently displayed.
      </p>
    </div>
  )
}