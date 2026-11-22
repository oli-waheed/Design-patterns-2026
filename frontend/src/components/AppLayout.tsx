import { Link, Outlet } from 'react-router-dom'
import ConnectionStatus from './ConnectionStatus'
import HealthStatus from './HealthStatus'

export default function AppLayout() {
  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-7xl flex-col gap-3 px-4 py-4 sm:flex-row sm:items-center sm:justify-between sm:px-6">
          <div>
            <h1 className="text-xl font-bold">Smart Greenhouse</h1>
            <p className="text-sm text-slate-500">
              Greenhouse monitoring and control
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <ConnectionStatus />
            <HealthStatus />
          </div>
        </div>

        <nav className="mx-auto flex max-w-7xl gap-6 px-4 pb-4 text-sm sm:px-6">
          <Link
            to="/"
            className="font-medium text-slate-700 hover:text-slate-900"
          >
            Home
          </Link>

          <Link
            to="/dashboard"
            className="font-medium text-slate-700 hover:text-slate-900"
          >
            Dashboard
          </Link>
        </nav>
      </header>

      <main className="mx-auto max-w-7xl px-4 py-6 sm:px-6 sm:py-8">
        <Outlet />
      </main>
    </div>
  )
}