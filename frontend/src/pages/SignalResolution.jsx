import { useState, useEffect, useMemo } from 'react'
import NoiseOverlay from '../components/NoiseOverlay'
import GlassPanel from '../components/GlassPanel'

const INITIAL_CATALYSTS = [
  { id: 1, time: '14:02:11', source: 'REUTERS', headline: 'Central bank hints at liquidity injection for Q4.' },
  { id: 2, time: '13:58:45', source: 'ON-CHAIN', headline: 'Whale accumulation detected in prime brokerage wallets.' },
  { id: 3, time: '13:45:20', source: 'SENTIMENT', headline: 'Retail fear levels hit 12-month highs, prime for reversal.' },
  { id: 4, time: '13:30:02', source: 'MACRO', headline: 'Tech sector yield curve flattening against expectations.' },
]

export default function SignalResolution() {
  const [currentTime, setCurrentTime] = useState('')
  const [catalysts] = useState(INITIAL_CATALYSTS)

  // Stable particle positions — computed once
  const inputParticles = useMemo(() =>
    Array.from({ length: 15 }, (_, i) => ({
      id: i,
      top: Math.random() * 100,
      delay: Math.random() * 4,
      duration: 3 + Math.random() * 2,
    })), []
  )

  const outputParticles = useMemo(() =>
    Array.from({ length: 8 }, (_, i) => ({
      id: i,
      top: 40 + Math.random() * 20,
      delay: Math.random() * 3,
      duration: 2 + Math.random() * 1,
    })), []
  )

  useEffect(() => {
    const tick = () => {
      const now = new Date()
      setCurrentTime(
        now.toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' }) + ' UTC'
      )
    }
    tick()
    const id = setInterval(tick, 1000)
    return () => clearInterval(id)
  }, [])

  return (
    <div className="relative min-h-screen overflow-x-hidden">
      <NoiseOverlay />
      <div className="vignette" />

      {/* Header HUD */}
      <header className="fixed top-0 left-0 w-full p-8 flex justify-between items-start z-50 pointer-events-none">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 border border-red-600 flex items-center justify-center rotate-45">
            <span className="text-[10px] font-black -rotate-45">RE</span>
          </div>
          <div>
            <h1 className="text-xs font-bold tracking-[0.4em] uppercase">Resonance Engine</h1>
            <p className="text-[9px] text-red-600 tracking-widest uppercase opacity-80">Signal Analysis Mode</p>
          </div>
        </div>

        <div className="flex gap-12 text-right">
          <div className="hidden md:block">
            <div className="label-mini">Encryption Node</div>
            <div className="text-[10px] font-mono uppercase">SEC-771.229.X</div>
          </div>
          <div>
            <div className="label-mini">System Time</div>
            <div className="text-[10px] font-mono">{currentTime}</div>
          </div>
        </div>
      </header>

      {/* Main */}
      <main className="relative z-10 pt-32 pb-24 px-8 max-w-7xl mx-auto">

        {/* Hero Section */}
        <section className="mb-16">
          <div className="flex justify-between items-end mb-6">
            <div>
              <span className="label-mini">Signal Identification</span>
              <h2 className="text-4xl font-black tracking-tighter uppercase mt-1">
                NV-992: <span className="text-red-600">Aggressive Accumulation</span>
              </h2>
            </div>
            <div className="text-right">
              <span className="label-mini">Confidence Score</span>
              <div className="text-3xl font-light tracking-widest text-white">98.4%</div>
            </div>
          </div>

          {/* Flow Map Panel */}
          <GlassPanel className="relative h-[400px] w-full overflow-hidden flex items-center justify-center">
            <div className="scan-bar" />

            {/* Background Grid */}
            <div
              className="absolute inset-0 opacity-10"
              style={{
                backgroundImage: 'linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px)',
                backgroundSize: '40px 40px',
              }}
            />

            {/* Particle Flow */}
            <div className="relative h-full w-full overflow-hidden">
              {/* Input particles (left → prism) */}
              {inputParticles.map(p => (
                <div
                  key={p.id}
                  className="data-particle data-stream-left"
                  style={{
                    top: `${p.top}%`,
                    width: '2px',
                    height: '2px',
                    animationDelay: `${p.delay}s`,
                    animationDuration: `${p.duration}s`,
                  }}
                />
              ))}

              {/* AI Prism Core */}
              <div className="prism-core">
                <div className="prism-inner" />
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="w-1 h-1 bg-white animate-ping" />
                </div>
              </div>

              {/* Output particles (prism → right) */}
              {outputParticles.map(p => (
                <div
                  key={p.id}
                  className="data-particle signal-stream-right"
                  style={{
                    top: `${p.top}%`,
                    width: '4px',
                    height: '4px',
                    animationDelay: `${p.delay}s`,
                    animationDuration: `${p.duration}s`,
                  }}
                />
              ))}
            </div>

            {/* Left Labels */}
            <div className="absolute left-10 top-1/2 -translate-y-1/2 space-y-4 z-10">
              {['Global Macro Feed', 'Sentiment Distortion', 'Order Book Liquidity'].map(label => (
                <div key={label} className="flex items-center gap-3 opacity-60 hover:opacity-100 transition-opacity">
                  <div className="w-2 h-px bg-white" />
                  <span className="text-[9px] uppercase tracking-widest">{label}</span>
                </div>
              ))}
            </div>

            {/* Right: Recommendation */}
            <div className="absolute right-10 top-1/2 -translate-y-1/2 text-right z-10">
              <div className="text-red-600 text-xs font-bold tracking-[0.3em] uppercase mb-1">Recommendation</div>
              <div className="text-2xl font-black tracking-tighter">LONG / OVERWEIGHT</div>
            </div>
          </GlassPanel>
        </section>

        {/* Bento Data Grid */}
        <div className="grid grid-cols-12 gap-6">

          {/* Chart Panel */}
          <GlassPanel className="col-span-12 lg:col-span-8 p-6">
            <div className="flex justify-between mb-8">
              <h3 className="label-mini text-white/60">Real-time Resonance Convergence</h3>
              <div className="flex gap-4">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-red-600" />
                  <span className="text-[9px] uppercase tracking-widest">Signal Delta</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-white/20" />
                  <span className="text-[9px] uppercase tracking-widest">Baseline</span>
                </div>
              </div>
            </div>

            <div className="h-64 w-full">
              <svg className="w-full h-full" preserveAspectRatio="none" viewBox="0 0 1000 200">
                <defs>
                  <linearGradient id="liquidGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="rgba(255, 51, 51, 0.4)" />
                    <stop offset="100%" stopColor="rgba(255, 51, 51, 0)" />
                  </linearGradient>
                  <filter id="liquid-distort">
                    <feTurbulence type="fractalNoise" baseFrequency="0.01 0.1" numOctaves="2" result="noise">
                      <animate attributeName="baseFrequency" dur="10s" values="0.01 0.1;0.015 0.15;0.01 0.1" repeatCount="indefinite" />
                    </feTurbulence>
                    <feDisplacementMap in="SourceGraphic" in2="noise" scale="5" />
                  </filter>
                </defs>
                <path className="liquid-chart-area" d="M0,200 L0,150 Q250,50 500,120 T1000,80 L1000,200 Z" />
                <path d="M0,150 Q250,50 500,120 T1000,80" fill="none" stroke="#ff3333" strokeWidth="2" opacity="0.8" />
              </svg>
            </div>
          </GlassPanel>

          {/* Catalysts Panel */}
          <GlassPanel className="col-span-12 lg:col-span-4 p-6">
            <h3 className="label-mini mb-6">Extraction Catalysts</h3>
            <div className="space-y-6">
              {catalysts.map(item => (
                <div key={item.id} className="group cursor-pointer">
                  <div className="flex justify-between items-start mb-1">
                    <span className="text-[10px] text-red-600 font-bold uppercase tracking-widest">{item.time}</span>
                    <span className="text-[9px] text-white/30">{item.source}</span>
                  </div>
                  <p className="text-xs font-light leading-relaxed group-hover:text-red-500 transition-colors">
                    {item.headline}
                  </p>
                  <div className="mt-2 h-px w-full bg-white/5 group-hover:bg-red-950 transition-colors" />
                </div>
              ))}
            </div>
            <button className="w-full mt-8 py-3 border border-white/10 text-[9px] uppercase tracking-[0.4em] hover:bg-white hover:text-black transition-all">
              Expand Raw Feed
            </button>
          </GlassPanel>

          {/* Volatility Vector */}
          <GlassPanel className="col-span-12 md:col-span-4 p-6 flex flex-col justify-between">
            <div>
              <span className="label-mini">Volatility Vector</span>
              <div className="text-3xl font-black mt-2 text-red-600">HIGH</div>
            </div>
            <div className="mt-8">
              <div className="flex justify-between text-[10px] mb-2">
                <span className="uppercase tracking-widest text-white/40">Entropy Scale</span>
                <span>0.88</span>
              </div>
              <div className="h-1 w-full bg-white/5">
                <div className="h-full bg-red-600 shadow-[0_0_10px_#ff3333]" style={{ width: '88%' }} />
              </div>
            </div>
          </GlassPanel>

          {/* Execution Window */}
          <GlassPanel className="col-span-12 md:col-span-4 p-6 flex flex-col justify-between">
            <div>
              <span className="label-mini">Execution Window</span>
              <div className="text-3xl font-black mt-2">14:00m</div>
            </div>
            <p className="text-[10px] text-white/40 uppercase tracking-widest leading-loose mt-4">
              Signal decay accelerates post-threshold. Immediate allocation advised.
            </p>
          </GlassPanel>

          {/* Engine Verdict */}
          <GlassPanel className="col-span-12 md:col-span-4 p-6 bg-red-600/5 border-red-600/30">
            <span className="label-mini text-red-500">Engine Verdict</span>
            <p className="text-sm font-medium mt-4 leading-relaxed">
              "Pattern matches historical Q3 squeeze dynamics. Resonance suggests a liquidity gap at $42.5k."
            </p>
            <div className="mt-6 flex gap-2">
              <div className="w-2 h-2 bg-red-600 rounded-full animate-pulse" />
              <span className="text-[9px] uppercase tracking-widest">Active Processing</span>
            </div>
          </GlassPanel>
        </div>
      </main>

      {/* Footer */}
      <footer className="fixed bottom-8 w-full px-12 flex justify-between items-end z-40 pointer-events-none opacity-40">
        <div className="text-[9px] uppercase tracking-[0.4em] max-w-xs leading-loose">
          Neural processing synchronized. <br />
          Current Load: 44.2 Teraflops.
        </div>
        <div className="flex gap-8 items-center">
          <div className="text-[9px] uppercase tracking-[0.4em]">Resonance Engine &copy; 2024</div>
          <div className="h-12 w-px bg-white/10" />
          <div className="flex flex-col items-end">
            <div className="text-[9px] uppercase tracking-[0.4em] mb-1">Sync Status</div>
            <div className="flex gap-1">
              {[0, 1, 2, 3].map(i => (
                <div key={i} className="w-4 h-[2px] bg-red-600" />
              ))}
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}
