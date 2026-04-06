import { Routes, Route } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import ProtectedRoute from './components/ProtectedRoute'
import AdminRoute from './components/AdminRoute'
import Landing from './pages/Landing'
import About from './pages/About'
import GateIgnition from './pages/GateIgnition'
import CommandCore from './pages/CommandCore'
import SignalResolution from './pages/SignalResolution'

import AdminLayout from './layouts/AdminLayout'
import AdminDashboard from './pages/admin/AdminDashboard'
import AdminUsers from './pages/admin/AdminUsers'
import AdminSignals from './pages/admin/AdminSignals'
import AdminEvents from './pages/admin/AdminEvents'
import AdminPipeline from './pages/admin/AdminPipeline'
import AdminSettings from './pages/admin/AdminSettings'

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/about" element={<About />} />
        <Route path="/login" element={<GateIgnition />} />
        <Route path="/dashboard" element={<ProtectedRoute><CommandCore /></ProtectedRoute>} />
        <Route path="/signal" element={<ProtectedRoute><SignalResolution /></ProtectedRoute>} />

        {/* Admin routes — will be protected by Clerk role check later */}
        <Route path="/admin" element={<AdminRoute><AdminLayout /></AdminRoute>}>
          <Route index element={<AdminDashboard />} />
          <Route path="users" element={<AdminUsers />} />
          <Route path="signals" element={<AdminSignals />} />
          <Route path="events" element={<AdminEvents />} />
          <Route path="pipeline" element={<AdminPipeline />} />
          <Route path="settings" element={<AdminSettings />} />
        </Route>
      </Routes>
    </AuthProvider>
  )
}
