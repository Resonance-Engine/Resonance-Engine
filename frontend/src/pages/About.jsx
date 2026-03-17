import { useNavigate } from 'react-router-dom'
import NoiseOverlay from '../components/NoiseOverlay'
import Navbar from '../components/Navbar'

const SYSTEM_STATS = [
  { label: 'Neural Nodes', value: '1,024' },
  { label: 'Data Sources', value: '340+' },
  { label: 'Signal Patterns', value: '88,200' },
  { label: 'Processing Load', value: '44.2 TF' },
]

const PRINCIPLES = [
  {
    title: 'Speed Over Noise',
    body: 'Every millisecond matters. The Engine is architected for sub-12ms signal delivery — because the edge lives at the threshold of perception.',
  },
  {
    title: 'Context Is Everything',
    body: 'Raw data is noise. Resonance cross-references macro, on-chain, sentiment, and order-book layers before surfacing a single signal.',
  },
  {
    title: 'Confidence-First',
    body: 'No signal ships without a confidence score. Pattern matches below 80% are suppressed. Only high-conviction opportunities reach the operator.',
  },
]

export default function About() {
  const navigate = useNavigate()

  return (
    <div className="bg-[#0a0a0a] text-white min-h-screen overflow-x-hidden" style={{ cursor: 'crosshair' }}>
      <NoiseOverlay />
      <Navbar />
      <div className="vignette" />

      {/* ── HEADER ── */}
      <section className="relative pt-40 pb-24 px-8 max-w-5xl mx-auto">
        <div className="flex items-center gap-3 mb-6 opacity-50">
          <div className="w-8 h-px bg-red-600" />
          <span className="text-[9px] uppercase tracking-[0.6em] text-gray-400">System Intelligence</span>
        </div>

        <h1 className="text-5xl md:text-7xl font-black tracking-tighter uppercase leading-none mb-6">
          The World Runs on<br />
          <span className="text-red-600">Resonance</span>
        </h1>

        <div className="w-12 h-px bg-red-600 mb-8 shadow-[0_0_10px_rgba(255,51,51,0.5)]" />

        <p className="text-sm text-gray-400 font-light leading-relaxed max-w-xl tracking-wide">
          Resonance Engine is a real-time market intelligence platform. It ingests global financial signals,
          processes them through a multi-layer neural architecture, and delivers high-conviction trade
          insights — before the market reacts.
        </p>
      </section>

      {/* ── STATS GRID ── */}
      <section className="border-y border-white/5 glass-panel mb-24">
        <div className="max-w-5xl mx-auto px-8 py-8 grid grid-cols-2 md:grid-cols-4 gap-8">
          {SYSTEM_STATS.map((s) => (
            <div key={s.label} className="text-center">
              <div className="text-2xl font-black monospaced text-red-500">{s.value}</div>
              <div className="text-[9px] uppercase tracking-[0.4em] text-gray-500 mt-1">{s.label}</div>
            </div>
          ))}
        </div>
      </section>

      {/* ── PRINCIPLES ── */}
      <section className="max-w-5xl mx-auto px-8 pb-24">
        <div className="mb-12">
          <span className="text-[9px] uppercase tracking-[0.6em] text-red-600">Core Principles</span>
          <h2 className="text-3xl font-black tracking-tighter uppercase mt-3">How We Think</h2>
        </div>

        <div className="space-y-4">
          {PRINCIPLES.map((p, i) => (
            <div key={p.title} className="glass-panel p-8 flex gap-8 items-start group hover:border-red-600/30 transition-all duration-500">
              <div className="text-[9px] monospaced text-white/10 font-black pt-1 shrink-0">0{i + 1}</div>
              <div>
                <div className="text-[10px] uppercase tracking-[0.5em] text-red-600 mb-3">{p.title}</div>
                <p className="text-xs text-gray-400 font-light leading-relaxed">{p.body}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* ── CTA ── */}
      <section className="max-w-5xl mx-auto px-8 pb-32 text-center">
        <div className="glass-panel p-16 relative overflow-hidden">
          {/* Background grid */}
          <div className="absolute inset-0 opacity-5"
            style={{ backgroundImage: 'linear-gradient(#fff 1px, transparent 1px), linear-gradient(90deg, #fff 1px, transparent 1px)', backgroundSize: '40px 40px' }} />

          <div className="relative z-10">
            <div className="w-1.5 h-1.5 bg-red-600 rounded-full animate-pulse mx-auto mb-6" />
            <h2 className="text-3xl font-black tracking-tighter uppercase mb-4">Ready to Access?</h2>
            <p className="text-[10px] uppercase tracking-[0.4em] text-gray-500 mb-10">
              Request credentials or authenticate to enter the Command Core.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <button
                onClick={() => navigate('/login')}
                className="btn-ignition px-10 py-4 text-[10px] tracking-[0.6em]"
              >
                Ignite Engine
              </button>
              <button className="px-10 py-4 text-[10px] tracking-[0.6em] uppercase border border-white/10 text-gray-400 hover:text-white hover:border-white/30 transition-all duration-300">
                Request Credentials
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* ── FOOTER ── */}
      <footer className="border-t border-white/5 glass-panel">
        <div className="max-w-5xl mx-auto px-8 py-8 flex flex-col md:flex-row justify-between items-center gap-6 opacity-40">
          <div className="text-[9px] uppercase tracking-[0.4em] leading-loose">
            Neural processing synchronized.<br />
            Current Load: 44.2 Teraflops.
          </div>
          <div className="flex gap-8 items-center">
            <div className="text-[9px] uppercase tracking-[0.4em]">Resonance Engine &copy; 2026</div>
            <div className="h-8 w-px bg-white/10" />
            <div className="flex gap-1">
              <div className="w-4 h-[2px] bg-red-600" />
              <div className="w-4 h-[2px] bg-red-600" />
              <div className="w-4 h-[2px] bg-red-600" />
              <div className="w-4 h-[2px] bg-white/20" />
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}
