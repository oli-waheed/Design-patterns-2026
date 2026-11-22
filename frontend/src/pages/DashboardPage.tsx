import { useState, type ReactNode } from 'react'

import EventFeed from '../components/alerts/EventFeed'
import ErrorBoundary from '../components/ui/ErrorBoundary'
import CommandPanel from '../features/actuators/CommandPanel'
import ExecutionLog from '../features/actuators/ExecutionLog'
import StrategyPanel from '../features/automation/StrategyPanel'
import DeviceFamilySwitcher from '../features/devices/DeviceFamilySwitcher'
import DeviceList from '../features/devices/DeviceList'
import SensorHistoryChart from '../features/history/SensorHistoryChart'
import LocationManager from '../features/locations/LocationManager'
import OverviewPanel from '../features/overview/OverviewPanel'
import SensorList from '../features/sensors/SensorList'

type DeviceFamily = 'simulation' | 'edge'

type Section = {
  id: string
  title: string
  description: string
  /** Full width on large screens; otherwise half width. */
  wide: boolean
  content: ReactNode
}

export default function DashboardPage() {
  const [deviceFamily, setDeviceFamily] =
    useState<DeviceFamily>('simulation')

  const sections: Section[] = [
    {
      id: 'overview',
      title: 'Overview',
      description: 'Current status of one location, its zones and devices.',
      wide: true,
      content: <OverviewPanel />,
    },
    {
      id: 'sensors',
      title: 'Sensors',
      description: 'Latest readings, recent trend and sampling settings.',
      wide: true,
      content: <SensorList />,
    },
    {
      id: 'history',
      title: 'History',
      description: 'Stored sensor readings over a time range.',
      wide: true,
      content: <SensorHistoryChart />,
    },
    {
      id: 'events',
      title: 'Events',
      description: 'Alerts from sensors and actuators, plus actuator execution history.',
      wide: true,
      content: (
        <>
          <EventFeed />
          <ExecutionLog />
        </>
      ),
    },
    {
      id: 'controls',
      title: 'Controls',
      description: 'Send commands to pumps and grow lights.',
      wide: true,
      content: <CommandPanel family={deviceFamily} />,
    },
    {
      id: 'automation',
      title: 'Automation',
      description: 'Choose and evaluate the irrigation strategy for a location.',
      wide: true,
      content: (
        <div className="mt-6">
          <StrategyPanel />
        </div>
      ),
    },
    {
      id: 'devices',
      title: 'Devices',
      description: 'Provision device families and assign devices to zones.',
      wide: false,
      content: (
        <div className="mt-6 space-y-4">
          <DeviceFamilySwitcher
            family={deviceFamily}
            onFamilyChange={setDeviceFamily}
            devices={[]}
          />

          <DeviceList family={deviceFamily} />
        </div>
      ),
    },
    {
      id: 'configuration',
      title: 'Configuration',
      description: 'Create and edit locations and their zones.',
      wide: false,
      content: (
        <div className="mt-6">
          <LocationManager />
        </div>
      ),
    },
  ]

  return (
    <section>
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-slate-900 sm:text-3xl">
          Dashboard
        </h2>

        <p className="mt-1 text-slate-600">
          Smart greenhouse monitoring and control.
        </p>
      </div>

      <nav
        aria-label="Dashboard sections"
        className="-mx-1 mb-6 flex gap-1 overflow-x-auto pb-1 text-sm"
      >
        {sections.map((section) => (
          <a
            key={section.id}
            href={`#${section.id}`}
            className="shrink-0 rounded-full px-3 py-1.5 font-medium text-slate-600 hover:bg-white hover:text-slate-900 hover:shadow-sm"
          >
            {section.title}
          </a>
        ))}
      </nav>

      <div className="grid gap-6 lg:grid-cols-2">
        {sections.map((section) => (
          <article
            key={section.id}
            id={section.id}
            className={`card min-w-0 scroll-mt-6 p-4 sm:p-6 ${
              section.wide ? 'lg:col-span-2' : ''
            }`}
          >
            <h3 className="section-title">{section.title}</h3>

            <p className="mt-1 text-muted">{section.description}</p>

            <ErrorBoundary name={section.title}>
              {section.content}
            </ErrorBoundary>
          </article>
        ))}
      </div>
    </section>
  )
}
