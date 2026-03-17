import { useRef, useEffect } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import NoiseOverlay from '../components/NoiseOverlay'
import Navbar from '../components/Navbar'
import LogoIntro from '../components/LogoIntro'
import Globe from '../components/Globe'

const FEATURES = [
  {
    id: 1,
    label: 'Signal Ingress',
    description: 'Raw market intelligence — news, on-chain flows, and macro data — ingested and filtered in real time.',
    icon: '→',
  },
  {
    id: 2,
    label: 'Resonance Core',
    description: 'Neural pattern recognition identifies high-probability setups across asset classes with 98%+ confidence scoring.',
    icon: '◈',
  },
  {
    id: 3,
    label: 'Execution Layer',
    description: 'Distilled trade signals delivered with entry vectors, volatility scores, and decay windows.',
    icon: '⬡',
  },
]

const STATS = [
  { label: 'Signal Accuracy', value: '98.4%' },
  { label: 'Assets Monitored', value: '4,200+' },
  { label: 'Latency', value: '<12ms' },
  { label: 'Uptime', value: '99.97%' },
]

export default function Landing() {
  const navigate = useNavigate()
  const location = useLocation()
  const navWrapRef = useRef(null)

  useEffect(() => {
    if (location.state?.skipIntro) {
      window.scrollTo({ top: window.innerHeight * 2.8, behavior: 'instant' })
    }
  }, [location.state])

  useEffect(() => {
    const handleScroll = () => {
      if (!navWrapRef.current) return
      const fadeStart = window.innerHeight * 1.5
      const fadeEnd   = window.innerHeight * 1.8
      const opacity   = Math.min(1, Math.max(0, (window.scrollY - fadeStart) / (fadeEnd - fadeStart)))
      navWrapRef.current.style.opacity       = opacity
      navWrapRef.current.style.pointerEvents = opacity > 0.05 ? 'auto' : 'none'
    }
    window.addEventListener('scroll', handleScroll, { passive: true })
    handleScroll()
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  return (
    <div className="bg-[#0a0a0a] text-white min-h-screen" style={{ cursor: 'crosshair' }}>
      <NoiseOverlay />

      {/* Navbar */}
      <div ref={navWrapRef} style={{ opacity: 0, pointerEvents: 'none', position: 'fixed', top: 0, left: 0, width: '100%', zIndex: 120 }}>
        <Navbar />
      </div>

      {/* Logo intro */}
      <div><LogoIntro /></div>

      {/* Vignette */}
      <div className="vignette" />

      {/* ── HERO ── */}
      <section id="hero" className="relative min-h-screen flex flex-row items-center overflow-hidden bg-[#0a0a0a]">

        {/* Left — text */}
        <div className="relative z-10 flex flex-col items-start justify-center px-16 w-full md:w-1/2 text-left min-h-screen py-20">

          <div className="flex-1 flex flex-col justify-center">
            <div className="flex items-center gap-3 mb-8 opacity-60">
              <div className="w-6 h-px bg-red-600" />
              <span className="text-[9px] uppercase tracking-[0.6em] text-gray-400">Neural Market Intelligence</span>
            </div>

            <h1 className="text-6xl md:text-8xl font-black tracking-tighter leading-none uppercase mb-5">
              Resonance<br />
              <span className="text-red-600">Engine</span>
            </h1>

            <p className="text-xs font-light tracking-[0.4em] uppercase text-gray-500 max-w-xs mb-10">
              Seek your Alpha.
            </p>

            <div className="w-10 h-px bg-red-600 mb-10 shadow-[0_0_12px_rgba(255,51,51,0.6)]" />

            <div className="flex flex-col sm:flex-row gap-3 items-start">
              <button
                onClick={() => navigate('/login')}
                className="btn-ignition px-10 py-4 text-[10px] tracking-[0.6em]"
              >
                Enter the Engine
              </button>
              <button
                onClick={() => navigate('/about')}
                className="px-10 py-4 text-[10px] tracking-[0.6em] uppercase border border-white/10 text-gray-500 hover:text-white hover:border-white/25 transition-all duration-300"
              >
                Learn More
              </button>
            </div>
          </div>

          {/* HUD status */}
          <div className="flex flex-col gap-1.5 opacity-30 pointer-events-none">
            <div className="flex items-center gap-2">
              <div className="w-1.5 h-1.5 bg-red-600 rounded-full animate-pulse" />
              <span className="text-[8px] uppercase tracking-[0.35em]">Engine Core: Standby</span>
            </div>
            <div className="text-[8px] uppercase tracking-[0.35em] text-gray-600 pl-3.5">
              SNR: 0.9982
            </div>
          </div>
        </div>

        {/* Right — globe */}
        <div className="absolute right-0 top-0 w-full md:w-[60%] h-full pointer-events-auto">
          <Globe />
          <div className="absolute inset-y-0 left-0 w-2/5 pointer-events-none"
            style={{ background: 'linear-gradient(to right, #0a0a0a 20%, transparent)' }} />
          <div className="absolute inset-y-0 right-0 w-12 pointer-events-none"
            style={{ background: 'linear-gradient(to left, #0a0a0a, transparent)' }} />
          <div className="absolute inset-x-0 top-0 h-32 pointer-events-none"
            style={{ background: 'linear-gradient(to bottom, #0a0a0a, transparent)' }} />
          <div className="absolute inset-x-0 bottom-0 h-32 pointer-events-none"
            style={{ background: 'linear-gradient(to top, #0a0a0a, transparent)' }} />
        </div>

        {/* Scroll hint */}
        <div className="absolute bottom-10 right-10 flex flex-col items-center gap-2 opacity-20 pointer-events-none z-10">
          <span className="text-[7px] uppercase tracking-[0.5em] text-gray-500">Scroll</span>
          <div className="w-px h-8 bg-gradient-to-b from-white/50 to-transparent" />
        </div>
      </section>

      {/* ── STATS BAR ── */}
      <section className="border-y border-white/[0.06] bg-[#0a0a0a]">
        <div className="max-w-5xl mx-auto px-8 py-8 grid grid-cols-2 md:grid-cols-4 gap-8">
          {STATS.map((s, i) => (
            <div key={s.label} className={`text-center ${i < 3 ? 'md:border-r border-white/[0.06]' : ''}`}>
              <div className="text-2xl font-black monospaced text-red-500 mb-1">{s.value}</div>
              <div className="text-[8px] uppercase tracking-[0.5em] text-gray-600">{s.label}</div>
            </div>
          ))}
        </div>
      </section>

      {/* ── FEATURE GRID ── */}
      <section className="max-w-6xl mx-auto px-8 py-28">
        <div className="text-center mb-16">
          <div className="flex items-center justify-center gap-3 mb-4">
            <div className="w-6 h-px bg-red-600/60" />
            <span className="text-[8px] uppercase tracking-[0.7em] text-red-600/80">How It Works</span>
            <div className="w-6 h-px bg-red-600/60" />
          </div>
          <h2 className="text-3xl font-black tracking-tighter uppercase">The Signal Pipeline</h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          {FEATURES.map((f, i) => (
            <div key={f.id}
              className="relative p-8 border border-white/[0.07] hover:border-red-600/25 transition-all duration-500 group"
              style={{ background: 'rgba(12,12,12,0.6)' }}>
              <div className="absolute top-5 right-5 text-[9px] monospaced text-white/8 font-black">0{i + 1}</div>
              <div className="w-9 h-9 border border-red-600/30 flex items-center justify-center mb-6 text-red-600 rotate-45 group-hover:border-red-600/60 group-hover:bg-red-600/8 transition-all duration-300">
                <span className="-rotate-45 text-base">{f.icon}</span>
              </div>
              <div className="text-[8px] uppercase tracking-[0.55em] text-red-600/80 mb-3">{f.label}</div>
              <p className="text-xs text-gray-500 leading-relaxed font-light">{f.description}</p>
              <div className="absolute bottom-0 left-0 w-0 h-px bg-red-600/60 group-hover:w-full transition-all duration-500" />
            </div>
          ))}
        </div>
      </section>

      {/* ── LOCKED PREVIEW ── */}
      <section className="max-w-6xl mx-auto px-8 pb-28">
        <div className="text-center mb-10">
          <div className="flex items-center justify-center gap-3 mb-4">
            <div className="w-6 h-px bg-red-600/60" />
            <span className="text-[8px] uppercase tracking-[0.7em] text-red-600/80">Restricted Access</span>
            <div className="w-6 h-px bg-red-600/60" />
          </div>
          <h2 className="text-3xl font-black tracking-tighter uppercase">Command Core Preview</h2>
        </div>

        <div className="relative border border-white/[0.07] overflow-hidden h-72 flex items-center justify-center bg-[#0a0a0a]">

          {/* Fake blurred dashboard */}
          <div className="absolute inset-0 pointer-events-none" style={{ filter: 'blur(3px)', opacity: 0.25 }}>
            <div className="absolute inset-0"
              style={{ backgroundImage: 'linear-gradient(rgba(255,255,255,0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.03) 1px, transparent 1px)', backgroundSize: '48px 48px' }} />
            <div className="flex gap-3 p-6 h-full">
              <div className="w-1/5 border border-white/10 rounded-sm" style={{ background: 'rgba(255,51,51,0.04)' }} />
              <div className="flex-1 border border-red-600/20 rounded-sm" style={{ background: 'rgba(255,51,51,0.03)' }} />
              <div className="w-1/5 border border-white/10 rounded-sm" style={{ background: 'rgba(255,255,255,0.02)' }} />
            </div>
          </div>

          {/* Dark gradient overlay */}
          <div className="absolute inset-0 pointer-events-none"
            style={{ background: 'radial-gradient(ellipse at center, rgba(10,10,10,0.5) 0%, rgba(10,10,10,0.85) 100%)' }} />

          {/* Lock */}
          <div className="relative z-10 text-center">
            <div className="w-7 h-7 border border-red-600/70 rotate-45 mx-auto mb-5 flex items-center justify-center">
              <span className="text-red-600 text-xs -rotate-45">⚿</span>
            </div>
            <p className="text-[9px] uppercase tracking-[0.55em] text-gray-500 mb-7">Access requires authentication</p>
            <button
              onClick={() => navigate('/login')}
              className="btn-ignition px-8 py-3 text-[9px] tracking-[0.5em]"
            >
              Ignite Engine
            </button>
          </div>
        </div>
      </section>

      {/* ── FOOTER ── */}
      <footer className="border-t border-white/[0.06]" style={{ background: 'rgba(8,8,8,0.95)' }}>
        <div className="max-w-6xl mx-auto px-8 py-8 flex flex-col md:flex-row justify-between items-center gap-6 opacity-35">
          <div className="text-[8px] uppercase tracking-[0.45em] leading-loose text-gray-600">
            High-frequency data extraction active.<br />
            Signal-to-noise ratio: 0.9982.
          </div>
          <div className="flex gap-8 items-center">
            <div className="flex flex-col items-end gap-1.5">
              <div className="text-[8px] uppercase tracking-[0.4em]">Grid Connectivity</div>
              <div className="flex gap-1">
                <div className="w-4 h-[2px] bg-red-600" />
                <div className="w-4 h-[2px] bg-red-600" />
                <div className="w-4 h-[2px] bg-red-600" />
                <div className="w-4 h-[2px] bg-white/15" />
              </div>
            </div>
            <div className="h-6 w-px bg-white/10" />
            <div className="text-[8px] uppercase tracking-[0.4em]">Resonance Engine &copy; 2026</div>
          </div>
        </div>
      </footer>
    </div>
  )
}
