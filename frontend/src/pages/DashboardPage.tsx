import { useState } from 'react'

import DeviceFamilySwitcher from '../features/devices/DeviceFamilySwitcher'
import DeviceList from '../features/devices/DeviceList'
import LocationManager from '../features/locations/LocationManager'
import SensorList from '../features/sensors/SensorList'

type DeviceFamily = 'simulation' | 'edge'

export default function DashboardPage() {
  const [deviceFamily, setDeviceFamily] =
    useState<DeviceFamily>('simulation')

  const sections = [
    {
      id: 'sensors',
      title: 'Sensors',
      description: 'Monitor greenhouse sensor readings.',
    },
    {
      id: 'devices',
      title: 'Devices',
      description: 'Manage simulation and edge devices.',
    },
    {
      id: 'configuration',
      title: 'Configuration',
      description: 'Configure greenhouse settings.',
    },
    {
      id: 'automation',
      title: 'Automation',
      description: 'Manage automated greenhouse actions.',
    },
    {
      id: 'overview',
      title: 'Overview',
      description: 'View the current greenhouse status.',
    },
    {
      id: 'controls',
      title: 'Controls',
      description: 'Control greenhouse equipment.',
    },
    {
      id: 'events',
      title: 'Events',
      description: 'View recent greenhouse events.',
    },
  ]

  return (
    <section>
      <div className="mb-8">
        <h2 className="text-3xl font-bold">
          Dashboard
        </h2>

        <p className="mt-2 text-gray-600">
          Smart greenhouse monitoring and control.
        </p>
      </div>

      <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
        {sections.map((section) => (
          <article
            key={section.id}
            id={section.id}
            className="rounded-xl border bg-white p-6 shadow-sm"
          >
            <h3 className="text-lg font-semibold">
              {section.title}
            </h3>

            <p className="mt-2 text-sm text-gray-600">
              {section.description}
            </p>

            {section.id === 'sensors' ? (
              <SensorList />
            ) : section.id === 'devices' ? (
              <div className="mt-6 space-y-4">
                <DeviceFamilySwitcher
                  family={deviceFamily}
                  onFamilyChange={setDeviceFamily}
                  devices={[]}
                />

                <DeviceList
                  family={deviceFamily}
                />
              </div>
            ) : section.id === 'configuration' ? (
              <div className="mt-6">
                <LocationManager />
              </div>
            ) : (
              <div className="mt-6 rounded-lg bg-gray-50 p-4 text-sm text-gray-500">
                Placeholder
              </div>
            )}
          </article>
        ))}
      </div>
    </section>
  )
}