import SensorList from '../features/sensors/SensorList'

export default function DashboardPage() {
  const sections = [
    {
      id: 'sensors',
      title: 'Sensors',
      description: 'Monitor greenhouse sensor readings.',
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
        <h2 className="text-3xl font-bold">Dashboard</h2>

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