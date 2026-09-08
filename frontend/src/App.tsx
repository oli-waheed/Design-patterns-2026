import { Routes, Route } from 'react-router-dom'
import AppLayout from './components/AppLayout'
import DashboardPage from './pages/DashboardPage'

function HomePage() {
  return (
    <section>
      <h2 className="text-3xl font-bold">Welcome to Smart Greenhouse</h2>

      <p className="mt-3 text-gray-600">
        Monitor and control your smart greenhouse from one place.
      </p>
    </section>
  )
}

export default function App() {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route path="/" element={<HomePage />} />
        <Route path="/dashboard" element={<DashboardPage />} />
      </Route>
    </Routes>
  )
}