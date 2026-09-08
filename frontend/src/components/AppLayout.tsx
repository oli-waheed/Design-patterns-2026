import { Link, Outlet } from 'react-router-dom'
import HealthStatus from './HealthStatus'

export default function AppLayout() {
  return (
    <div className="min-h-screen bg-gray-50 text-gray-900">
      <header className="border-b bg-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
          <div>
            <h1 className="text-xl font-bold">Smart Greenhouse</h1>
            <p className="text-sm text-gray-500">
              Greenhouse monitoring and control
            </p>
          </div>

          <HealthStatus />
        </div>

        <nav className="mx-auto flex max-w-7xl gap-6 px-6 pb-4 text-sm">
          <Link
            to="/"
            className="font-medium text-gray-700 hover:text-gray-900"
          >
            Home
          </Link>

          <Link
            to="/dashboard"
            className="font-medium text-gray-700 hover:text-gray-900"
          >
            Dashboard
          </Link>
        </nav>
      </header>

      <main className="mx-auto max-w-7xl px-6 py-8">
        <Outlet />
      </main>
    </div>
  )
}