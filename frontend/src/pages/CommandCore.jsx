import { useState, useEffect, useRef } from 'react'
import NoiseOverlay from '../components/NoiseOverlay'
import GlassPanel from '../components/GlassPanel'

const INITIAL_SIGNALS = [
  { id: 1, time: '14:22:01', headline: 'FED CHAIR INDICATES RATE PAUSE UNTIL Q4', asset: 'DXY', strength: 92, impact: 'HIGH VOLATILITY' },
  { id: 2, time: '14:21:44', headline: 'TSMC REPORTS RECORD CHIP DEMAND IN AI SECTOR', asset: 'NVDA', strength: 84, impact: 'BULLISH BIAS' },
  { id: 3, time: '14:20:12', headline: 'OIL PIPELINE DISRUPTION IN NORTH SEA REGION', asset: 'BRENT', strength: 67, impact: 'SUPPLY SQUEEZE' },
  { id: 4, time: '14:18:55', headline: 'EU REGULATORS APPROVE NEW FINTECH FRAMEWORK', asset: 'EUR', strength: 45, impact: 'NEUTRAL' },
]

const INITIAL_LOGS = [
  { id: 1, time: '[14:22:10]', msg: 'Inbound signal hash verified.' },
  { id: 2, time: '[14:22:15]', msg: 'Processing semantic layers...' },
  { id: 3, time: '[14:22:18]', msg: 'Volatility resonance detected at 0.88Hz' },
  { id: 4, time: '[14:22:25]', msg: 'Executing predictive logic branch α.' },
]

const ASSETS = ['BTC', 'GOLD', 'AAPL', 'TSLA']
const HEADLINES = [
  'Market liquidity depth decreasing',
  'Neural net identifies pattern 7G',
  'Volume spike detected in retail flow',
  'Cross-asset correlation rising',
]

function TickerBlock() {
  return (
    <div className="flex gap-8">
      <div className="flex items-center gap-2">
        <span className="text-[10px] font-bold">BTC/USD</span>
        <span className="text-[10px] text-green-500 monospaced">64,210.44 (+1.2%)</span>
      </div>
      <div className="flex items-center gap-2">
        <span className="text-[10px] font-bold">ETH/USD</span>
        <span className="text-[10px] text-red-500 monospaced">3,412.10 (-0.4%)</span>
      </div>
      <div className="flex items-center gap-2">
        <span className="text-[10px] font-bold">SPY</span>
        <span className="text-[10px] text-green-500 monospaced">512.11 (+0.8%)</span>
      </div>
    </div>
  )
}

export default function CommandCore() {
  const [volatility, setVolatility] = useState(64)
  const [sessionTime, setSessionTime] = useState('00:00:00')
  const [signals, setSignals] = useState(INITIAL_SIGNALS)
  const [logs, setLogs] = useState(INITIAL_LOGS)
  const [chartData, setChartData] = useState([40, 55, 45, 60, 80, 75, 90, 85, 70, 65, 80, 95, 85, 70, 60])
  const pnl = '12,440.00'
  const startTimeRef = useRef(Date.now())

  useEffect(() => {
    const id = setInterval(() => {
      // Session timer
      const elapsed = Math.floor((Date.now() - startTimeRef.current) / 1000)
      const h = String(Math.floor(elapsed / 3600)).padStart(2, '0')
      const m = String(Math.floor((elapsed % 3600) / 60)).padStart(2, '0')
      const s = String(elapsed % 60).padStart(2, '0')
      setSessionTime(`${h}:${m}:${s}`)

      // Volatility fluctuation
      setVolatility(prev =>
        parseFloat(Math.max(40, Math.min(95, prev + (Math.random() - 0.5) * 5)).toFixed(1))
      )

      // Chart bars
      setChartData(prev => prev.map(() => Math.floor(Math.random() * 100)))

      // Random signal injection
      if (Math.random() > 0.95) {
        const newSignal = {
          id: Date.now(),
          time: new Date().toLocaleTimeString('en-US', { hour12: false }),
          headline: HEADLINES[Math.floor(Math.random() * HEADLINES.length)],
          asset: ASSETS[Math.floor(Math.random() * ASSETS.length)],
          strength: Math.floor(Math.random() * 40) + 60,
          impact: 'LIVE UPDATE',
        }
        setSignals(prev => [newSignal, ...prev].slice(0, 10))

        const newLog = {
          id: Date.now(),
          time: `[${new Date().toLocaleTimeString('en-US', { hour12: false })}]`,
          msg: 'Signal cluster synchronized.',
        }
        setLogs(prev => [newLog, ...prev].slice(0, 8))
      }
    }, 1000)

    return () => clearInterval(id)
  }, [])

  return (
    <div className="relative h-screen flex flex-col p-6 gap-6 overflow-hidden">
      <NoiseOverlay />

      {/* HUD Background Decor */}
      <div className="fixed inset-0 pointer-events-none opacity-20">
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] border border-white/5 rounded-full" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[1200px] h-[1200px] border border-white/5 rounded-full" />
      </div>

      {/* Header */}
      <header className="relative z-10 flex justify-between items-start">
        <div className="flex gap-12">
          <div className="space-y-1">
            <div className="text-[10px] uppercase tracking-[0.4em] text-gray-500 font-bold">Resonance Engine</div>
            <div className="text-2xl font-black tracking-tighter flex items-center gap-3">
              <div className="w-2 h-6 bg-red-600" />
              COMMAND CORE <span className="text-red-600 text-xs font-light tracking-[0.2em] ml-2">v4.0.1</span>
            </div>
          </div>

          <div className="hidden lg:flex gap-8 border-l border-white/10 pl-8 items-center">
            <div className="space-y-1">
              <div className="text-[9px] uppercase tracking-widest text-gray-600">Sync Status</div>
              <div className="flex items-center gap-2">
                <div className="w-1.5 h-1.5 bg-red-600 rounded-full animate-pulse" />
                <div className="text-[11px] monospaced uppercase tracking-wider">Neural Link Active</div>
              </div>
            </div>
            <div className="space-y-1">
              <div className="text-[9px] uppercase tracking-widest text-gray-600">Global Volatility</div>
              <div className="text-[11px] monospaced uppercase tracking-wider text-red-500">{volatility}%</div>
            </div>
          </div>
        </div>

        <div className="text-right">
          <div className="text-[10px] uppercase tracking-[0.5em] text-gray-500 mb-1">Session Duration</div>
          <div className="text-xl monospaced font-light">{sessionTime}</div>
        </div>
      </header>

      {/* Main Grid */}
      <div className="relative z-10 flex-grow grid grid-cols-12 gap-6 overflow-hidden">

        {/* Left Sidebar: Signal Feed */}
        <aside className="col-span-12 lg:col-span-3 flex flex-col gap-4 overflow-hidden">
          <div className="flex items-center justify-between px-2">
            <h3 className="text-[10px] uppercase tracking-[0.5em] text-gray-400">Intelligence Feed</h3>
            <div className="text-[9px] text-red-500 font-bold px-2 py-0.5 border border-red-500/30">LIVE</div>
          </div>

          <GlassPanel className="flex-grow overflow-y-auto p-4 space-y-4">
            <div className="scan-line-horizontal" />
            {signals.map(signal => (
              <div
                key={signal.id}
                className="group relative p-3 border border-white/5 hover:border-red-500/40 transition-all duration-300 cursor-pointer bg-white/[0.02]"
              >
                <div className="flex justify-between items-start mb-2">
                  <span className="text-[10px] monospaced text-gray-500">{signal.time}</span>
                  <span className={`text-[9px] uppercase font-bold tracking-widest ${signal.strength > 80 ? 'text-red-500' : 'text-gray-400'}`}>
                    {signal.strength}% STRENGTH
                  </span>
                </div>
                <div className="text-xs font-bold leading-relaxed mb-1">{signal.headline}</div>
                <div className="flex gap-2">
                  <span className="text-[9px] bg-red-600/10 text-red-500 px-1.5 py-0.5 border border-red-600/20">{signal.asset}</span>
                  <span className="text-[9px] text-gray-500 py-0.5 tracking-tighter">{signal.impact}</span>
                </div>
              </div>
            ))}
          </GlassPanel>
        </aside>

        {/* Center: Resonance Core */}
        <main className="col-span-12 lg:col-span-6 glass-panel relative flex items-center justify-center">
          <div className="panel-accent" />

          {/* Background Grid */}
          <div
            className="absolute inset-0 opacity-10"
            style={{ backgroundImage: 'linear-gradient(#fff 1px, transparent 1px), linear-gradient(90deg, #fff 1px, transparent 1px)', backgroundSize: '40px 40px' }}
          />

          <div className="relative w-full h-full flex items-center justify-center">
            {/* SVG Resonance Waves */}
            <svg
              className="absolute w-full h-full opacity-60"
              viewBox="0 0 1000 1000"
              style={{ filter: 'url(#liquid-filter-cc)' }}
            >
              <defs>
                <filter id="liquid-filter-cc">
                  <feTurbulence type="fractalNoise" baseFrequency="0.012" numOctaves="3" seed="2">
                    <animate attributeName="baseFrequency" dur="15s" values="0.012;0.018;0.012" repeatCount="indefinite" />
                  </feTurbulence>
                  <feDisplacementMap in="SourceGraphic" scale="40" />
                </filter>
              </defs>
              <path d="M -100,500 Q 250,300 500,500 T 1100,500" fill="none" stroke="#ff3333" strokeWidth="4" opacity="0.8">
                <animate attributeName="d" dur="10s" repeatCount="indefinite" values="M -100,500 Q 250,300 500,500 T 1100,500; M -100,500 Q 250,700 500,500 T 1100,500; M -100,500 Q 250,300 500,500 T 1100,500" />
              </path>
              <path d="M -100,500 Q 250,600 500,500 T 1100,500" fill="none" stroke="#ff3333" strokeWidth="2" opacity="0.4">
                <animate attributeName="d" dur="8s" repeatCount="indefinite" values="M -100,500 Q 250,600 500,500 T 1100,500; M -100,500 Q 250,400 500,500 T 1100,500; M -100,500 Q 250,600 500,500 T 1100,500" />
              </path>
            </svg>

            {/* Geometric Overlay */}
            <div className="relative z-20">
              <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-80 h-80 border border-white/10 rotate-45 animate-[spin_20s_linear_infinite]" />
              <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[340px] h-[340px] border border-red-600/20 rotate-12 animate-[spin_40s_linear_infinite_reverse]" />

              {/* Diamond Core */}
              <div className="relative w-48 h-48 diamond-clip border border-red-500 bg-red-600/10 flex items-center justify-center overflow-hidden">
                <div className="absolute inset-0 bg-gradient-to-br from-red-600/40 to-transparent" />
                <div className="scan-line-horizontal" />
                <div className="relative z-10 text-center">
                  <div className="text-[10px] uppercase tracking-[0.4em] font-light opacity-60">Engine Load</div>
                  <div className="text-4xl font-black">{Math.floor(volatility * 0.8)}%</div>
                </div>
              </div>

              {/* Signal Ingress Pointer */}
              <div className="absolute -top-24 left-1/2 -translate-x-1/2 text-center">
                <div className="text-[9px] uppercase tracking-[0.5em] text-red-500 mb-2">Signal Ingress</div>
                <div className="h-16 w-px bg-gradient-to-b from-red-600 to-transparent mx-auto" />
              </div>
            </div>

            {/* Bottom HUD */}
            <div className="absolute bottom-8 left-8 right-8 flex justify-between items-end">
              <div className="space-y-2">
                <div className="text-[10px] uppercase tracking-[0.3em] text-gray-500">Processing Stream</div>
                <div className="flex gap-1">
                  {chartData.map((val, i) => (
                    <div key={i} className="w-1.5 h-4 bg-white/5 relative">
                      <div
                        className="absolute bottom-0 w-full bg-red-600 transition-all duration-500"
                        style={{ height: `${val}%` }}
                      />
                    </div>
                  ))}
                </div>
              </div>
              <div className="text-right">
                <div className="text-[10px] uppercase tracking-[0.3em] text-gray-500">Current Vector</div>
                <div className="text-lg monospaced font-bold text-red-500">α-779.22</div>
              </div>
            </div>
          </div>
        </main>

        {/* Right Sidebar */}
        <aside className="col-span-12 lg:col-span-3 flex flex-col gap-6 overflow-hidden">

          {/* Yield Architecture */}
          <GlassPanel className="p-5 flex flex-col gap-6">
            <div className="panel-accent" style={{ left: 'auto', right: 0 }} />
            <div className="text-[10px] uppercase tracking-[0.5em] text-gray-400">Yield Architecture</div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1">
                <div className="text-[9px] text-gray-600 uppercase">Real-time PnL</div>
                <div className="text-xl monospaced font-bold text-green-500">+${pnl}</div>
              </div>
              <div className="space-y-1">
                <div className="text-[9px] text-gray-600 uppercase">Active Risk</div>
                <div className="text-xl monospaced font-bold text-red-500">LOW</div>
              </div>
            </div>

            <div className="h-24 w-full flex items-end gap-1 px-1">
              {chartData.map((val, i) => (
                <div key={i} className="flex-grow bg-white/5 border-t border-white/10 relative group">
                  <div
                    className="absolute bottom-0 w-full bg-red-600/30 group-hover:bg-red-500 transition-all"
                    style={{ height: `${val}%` }}
                  />
                </div>
              ))}
            </div>
          </GlassPanel>

          {/* Neural Activity Logs */}
          <GlassPanel className="flex-grow p-5">
            <div className="text-[10px] uppercase tracking-[0.5em] text-gray-400 mb-4">Neural Activity Logs</div>
            <div className="space-y-3 font-mono text-[10px] text-gray-500 h-[200px] overflow-hidden">
              {logs.map(log => (
                <div key={log.id} className="flex gap-3">
                  <span className="text-red-900">{log.time}</span>
                  <span className="text-gray-400">{log.msg}</span>
                </div>
              ))}
              <div className="animate-pulse">_ EXECUTION BUFFER READY</div>
            </div>
          </GlassPanel>

          {/* Manual Override */}
          <button className="w-full bg-transparent border border-red-600/50 hover:bg-red-600 hover:text-black py-4 text-[10px] uppercase tracking-[0.8em] font-black transition-all group overflow-hidden relative">
            <span className="relative z-10">Manual Override</span>
            <div className="absolute inset-0 translate-y-full group-hover:translate-y-0 bg-red-600 transition-transform duration-300" />
          </button>
        </aside>
      </div>

      {/* Footer Ticker */}
      <footer className="relative z-10 h-12 glass-panel flex items-center px-6 gap-8 overflow-hidden">
        <div className="text-[10px] uppercase tracking-widest font-black text-red-600 whitespace-nowrap">Global Markets //</div>
        <div className="flex gap-12 animate-[marquee_30s_linear_infinite] whitespace-nowrap">
          {Array.from({ length: 10 }, (_, i) => <TickerBlock key={i} />)}
        </div>
      </footer>
    </div>
  )
}
