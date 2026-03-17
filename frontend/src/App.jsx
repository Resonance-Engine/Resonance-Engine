import { Routes, Route } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import ProtectedRoute from './components/ProtectedRoute'
import Landing from './pages/Landing'
import About from './pages/About'
import GateIgnition from './pages/GateIgnition'
import CommandCore from './pages/CommandCore'
import SignalResolution from './pages/SignalResolution'

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/about" element={<About />} />
        <Route path="/login" element={<GateIgnition />} />
        <Route path="/dashboard" element={<ProtectedRoute><CommandCore /></ProtectedRoute>} />
        <Route path="/signal" element={<ProtectedRoute><SignalResolution /></ProtectedRoute>} />
      </Routes>
    </AuthProvider>
  )
}
