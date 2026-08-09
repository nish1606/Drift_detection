import { useEffect, useState } from 'react'
import { BrowserRouter, Navigate, Route, Routes, useLocation, useNavigate } from 'react-router-dom'
import { canAccessRoute, getDefaultRoute } from './appConfig'
import Sidebar from './components/Sidebar'
import TopBar from './components/TopBar'
import AuditLog from './pages/AuditLog'
import DriftMonitoring from './pages/DriftMonitoring'
import Explainability from './pages/Explainability'
import FairnessMonitoring from './pages/FairnessMonitoring'
import Overview from './pages/Overview'
import Policies from './pages/Policies'
import ReviewQueue from './pages/ReviewQueue'
import Login from './pages/Login'
import { isAuthenticated, getRole, login as apiLogin } from './mockApi'

function AppFrame({ role, onRoleChange }) {
  const location = useLocation()
  const navigate = useNavigate()
  const [darkMode, setDarkMode] = useState(false)

  useEffect(() => {
    if (!canAccessRoute(role, location.pathname)) {
      navigate(getDefaultRoute(role), { replace: true })
    }
  }, [location.pathname, navigate, role])

  useEffect(() => {
    document.documentElement.classList.toggle('dark', darkMode)
  }, [darkMode])

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 transition-colors duration-300 dark:bg-slate-950 dark:text-slate-50">
      <div className="grid min-h-screen lg:grid-cols-[18rem_1fr]">
        <div className="hidden lg:block">
          <Sidebar role={role} />
        </div>

        <div className="flex min-w-0 flex-col">
          <TopBar role={role} onRoleChange={onRoleChange} darkMode={darkMode} onDarkModeChange={setDarkMode} />
          <main className="min-w-0 flex-1 p-4 lg:p-6">
            <Routes>
              <Route path="/" element={<Overview role={role} darkMode={darkMode} />} />
              <Route path="/review" element={<ReviewQueue role={role} darkMode={darkMode} />} />
              <Route path="/drift" element={canAccessRoute(role, '/drift') ? <DriftMonitoring role={role} darkMode={darkMode} /> : <Navigate to={getDefaultRoute(role)} replace />} />
              <Route path="/explainability" element={canAccessRoute(role, '/explainability') ? <Explainability role={role} darkMode={darkMode} /> : <Navigate to={getDefaultRoute(role)} replace />} />
              <Route path="/fairness" element={canAccessRoute(role, '/fairness') ? <FairnessMonitoring role={role} darkMode={darkMode} /> : <Navigate to={getDefaultRoute(role)} replace />} />
              <Route path="/policies" element={canAccessRoute(role, '/policies') ? <Policies role={role} darkMode={darkMode} /> : <Navigate to={getDefaultRoute(role)} replace />} />
              <Route path="/audit" element={canAccessRoute(role, '/audit') ? <AuditLog role={role} darkMode={darkMode} /> : <Navigate to={getDefaultRoute(role)} replace />} />
              <Route path="*" element={<Navigate to={getDefaultRoute(role)} replace />} />
            </Routes>
          </main>
        </div>
      </div>

      <div className="border-t border-slate-200 bg-white px-4 py-3 text-sm text-slate-500 dark:border-slate-800 dark:bg-slate-950 dark:text-slate-400 lg:hidden">
        Mobile view is intentionally simplified for internal laptop workstations.
      </div>
    </div>
  )
}

export default function App() {
  const [role, setRole] = useState(() => getRole() || 'Analyst')
  const [authed, setAuthed] = useState(() => isAuthenticated())

  useEffect(() => {
    setAuthed(isAuthenticated())
  }, [role])

  if (!authed) {
    return (
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login onLogin={() => { setRole(getRole()); setAuthed(true) }} />} />
          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
      </BrowserRouter>
    )
  }

  const handleRoleChange = async (nextRole) => {
    if (nextRole === role) return
    const credentials = {
      Analyst: { username: 'analyst', password: 'analyst123' },
      RiskEngineer: { username: 'risk_engineer', password: 'risk123' },
      Compliance: { username: 'compliance', password: 'compliance123' },
    }
    const creds = credentials[nextRole]
    if (creds) {
      await apiLogin(creds.username, creds.password)
      setRole(nextRole)
    }
  }

  return (
    <BrowserRouter>
      <AppFrame role={role} onRoleChange={handleRoleChange} />
    </BrowserRouter>
  )
}
