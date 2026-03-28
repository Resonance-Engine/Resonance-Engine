import { useState, useEffect, useRef } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import NoiseOverlay from '../components/NoiseOverlay'
import FloatingLetters from '../components/FloatingLetters'
import { useAuth } from '../context/AuthContext'

function generateParticles() {
  return Array.from({ length: 40 }, (_, i) => ({
    id: i,
    x: Math.random() * 100,
    y: Math.random() * 100,
    size: Math.random() * 2 + 1,
    speed: Math.random() * 2 + 1,
    parallax: Math.random() * 20 + 10,
  }))
}

export default function GateIgnition() {
  const navigate = useNavigate()
  const { isAuthenticated, login } = useAuth()
  const [ignited, setIgnited] = useState(false)
  const [isHovered, setIsHovered] = useState(false)
  const [currentTime, setCurrentTime] = useState('')
  const [mouseOffset, setMouseOffset] = useState({ x: 0, y: 0 })
  const [particles] = useState(generateParticles)
  const [visible, setVisible] = useState(false)
  const rafRef = useRef(null)

  useEffect(() => {
    if (isAuthenticated) navigate('/dashboard', { replace: true })
  }, [isAuthenticated, navigate])

  useEffect(() => {
    // Mount transition
    const t = setTimeout(() => setVisible(true), 50)

    // Clock
    const tick = () => {
      const now = new Date()
      setCurrentTime(
        now.toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' }) + ' UTC'
      )
    }
    tick()
    const id = setInterval(tick, 1000)

    return () => {
      clearTimeout(t)
      clearInterval(id)
    }
  }, [])

  const handleMouseMove = (e) => {
    if (rafRef.current) cancelAnimationFrame(rafRef.current)
    rafRef.current = requestAnimationFrame(() => {
      setMouseOffset({
        x: (e.clientX - window.innerWidth / 2) / 25,
        y: (e.clientY - window.innerHeight / 2) / 25,
      })
    })
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    setIgnited(true)
    setTimeout(() => {
      login()
      navigate('/dashboard')
    }, 3000)
  }

  return (
    <div
      className="relative min-h-screen overflow-hidden"
      onMouseMove={handleMouseMove}
    >
      <FloatingLetters mode="drift" />
      <NoiseOverlay />
      <div className="vignette" />

      {/* Parallax Particles */}
      <div className="fixed inset-0 pointer-events-none">
        {particles.map(p => (
          <div
            key={p.id}
            className="particle"
            style={{
              left: `${p.x}%`,
              top: `${p.y}%`,
              width: `${p.size}px`,
              height: `${p.size}px`,
              transition: `transform ${p.speed}s linear`,
              transform: `translate(${mouseOffset.x * p.parallax}px, ${mouseOffset.y * p.parallax}px)`,
            }}
          />
        ))}
      </div>

      {/* Top Left HUD */}
      <div className="absolute top-12 left-12 flex flex-col gap-3 z-50">
        <Link to="/" className="flex items-center gap-2 opacity-60 hover:opacity-100 transition-opacity group">
          <div className="w-1 h-4 bg-red-600" />
          <span className="text-[9px] uppercase tracking-[0.4em] group-hover:text-red-500 transition-colors">← Home</span>
        </Link>
        <div className="flex flex-col gap-1 opacity-40">
          <div className="text-[10px] uppercase tracking-[0.5em]">System Status</div>
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse" />
            <div className="text-[10px] uppercase tracking-[0.2em] font-light">Engine Core: Standby</div>
          </div>
        </div>
      </div>

      {/* Top Right HUD */}
      <div className="absolute top-12 right-12 text-right opacity-40 z-10">
        <div className="text-[10px] uppercase tracking-[0.5em]">Resonance v.4.0.1</div>
        <div className="text-[10px] uppercase tracking-[0.2em] font-light">{currentTime}</div>
      </div>

      {/* Main Content */}
      <main className="relative z-10 min-h-screen flex flex-col items-center justify-center px-6">

        {/* Outer Rings */}
        <div className="relative flex items-center justify-center mb-16">
          <div className="absolute w-[500px] h-[500px] border border-white/5 rounded-full opacity-20 animate-[spin_60s_linear_infinite]" />
          <div className="absolute w-[450px] h-[450px] border border-white/10 rotate-45 opacity-10" />

          {/* Diamond Portal */}
          <div
            className="diamond-container"
            style={{ transform: `rotate(45deg) scale(${isHovered ? 1.05 : 1})` }}
            onMouseEnter={() => setIsHovered(true)}
            onMouseLeave={() => setIsHovered(false)}
          >
            <div className="hyper-border" />
            <div className="diamond-inner">
              <div className="scanning-line" />
              <div className="liquid-core" />

              {/* SVG Wave Distortion */}
              <svg className="wave-svg" viewBox="0 0 100 100" preserveAspectRatio="none">
                <defs>
                  <filter id="liquid-filter-gi">
                    <feTurbulence type="fractalNoise" baseFrequency="0.015" numOctaves="3" seed="1">
                      <animate attributeName="baseFrequency" dur="10s" values="0.015;0.025;0.015" repeatCount="indefinite" />
                    </feTurbulence>
                    <feDisplacementMap in="SourceGraphic" scale="15" />
                  </filter>
                </defs>
                <g filter="url(#liquid-filter-gi)">
                  <rect width="100" height="100" fill="transparent" />
                  <circle cx="50" cy="50" r="30" fill="rgba(255,51,51,0.5)" />
                </g>
              </svg>

              {/* Core Symbol */}
              <div className="relative z-20 -rotate-45">
                <h1 className="text-4xl font-black tracking-tighter text-white mix-blend-difference">RE</h1>
              </div>
            </div>
          </div>
        </div>

        {/* Login Form */}
        {!ignited && (
          <div
            className={`w-full max-w-sm transition-all duration-1000 ${visible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10'}`}
          >
            <div className="text-center mb-12">
              <h2 className="text-xs uppercase tracking-[0.8em] font-light text-gray-500 mb-2">Intelligence Access</h2>
              <div className="h-px w-12 bg-red-600 mx-auto" />
            </div>

            <form onSubmit={handleSubmit} className="space-y-10">
              <div>
                <label className="sci-fi-label">Operator Identity</label>
                <input type="text" className="sci-fi-input" placeholder="Enter identification code" required />
              </div>

              <div>
                <label className="sci-fi-label">Neural Key</label>
                <input type="password" className="sci-fi-input" placeholder="••••••••" required />
              </div>

              <div className="flex flex-col items-center gap-6 pt-4">
                <button type="submit" className="btn-ignition group overflow-hidden">
                  <span className="relative z-10 glitch-text">Envoke Engine</span>
                  <div className="absolute inset-0 bg-white/10 translate-y-full group-hover:translate-y-0 transition-transform duration-300" />
                </button>
                <a href="#" className="text-[10px] uppercase tracking-[0.3em] text-gray-600 hover:text-red-500 transition-colors">
                  Request Credentials
                </a>
              </div>
            </form>
          </div>
        )}

        {/* Post-Ignition Loading */}
        {ignited && (
          <div className="text-center space-y-6">
            <div className="text-2xl font-light tracking-[0.5em] text-white animate-pulse">SYNCHRONIZING</div>
            <div className="flex gap-2 justify-center">
              {[0, 1, 2, 3, 4].map(i => (
                <div key={i} className="w-12 h-1 bg-red-600/20 relative overflow-hidden">
                  <div
                    className="absolute inset-0 bg-red-600"
                    style={{ animation: 'loading 2s infinite', animationDelay: `${i * 0.2}s` }}
                  />
                </div>
              ))}
            </div>
            <p className="text-[10px] text-gray-500 uppercase tracking-widest">
              Bridging neural pathways to real-time market news...
            </p>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="fixed bottom-8 w-full px-12 flex justify-between items-end z-10 pointer-events-none opacity-30">
        <div className="text-[9px] uppercase tracking-[0.4em] max-w-xs leading-loose">
          High-frequency data extraction active. <br />
          Signal-to-noise ratio: 0.9982.
        </div>
        <div className="flex gap-8 items-center">
          <div className="flex flex-col items-end">
            <div className="text-[9px] uppercase tracking-[0.4em] mb-1">Grid Connectivity</div>
            <div className="flex gap-1">
              <div className="w-4 h-[2px] bg-red-600" />
              <div className="w-4 h-[2px] bg-red-600" />
              <div className="w-4 h-[2px] bg-red-600" />
              <div className="w-4 h-[2px] bg-white/20" />
            </div>
          </div>
          <div className="h-12 w-px bg-white/10" />
          <div className="text-[9px] uppercase tracking-[0.4em]">Resonance Engine &copy; 2026</div>
        </div>
      </footer>
    </div>
  )
}
