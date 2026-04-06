import { useState } from 'react'

const SETTINGS = [
  { section: 'API Keys', items: [
    { key: 'openai',        label: 'OpenAI API Key',          value: 'sk-...7f3a',       masked: true },
    { key: 'pinecone',      label: 'Pinecone API Key',        value: 'pc-...9b2c',       masked: true },
    { key: 'alpha_vantage', label: 'Alpha Vantage Key',       value: 'AV-...4d1e',       masked: true },
    { key: 'finnhub',       label: 'Finnhub API Key',         value: 'fh-...8a3f',       masked: true },
    { key: 'newsapi',       label: 'NewsAPI Key',             value: 'na-...2c7b',       masked: true },
  ]},
  { section: 'Pipeline', items: [
    { key: 'edgar_interval',  label: 'EDGAR Scan Interval',     value: '15 min',     type: 'text' },
    { key: 'gdelt_interval',  label: 'GDELT Scan Interval',     value: '60 min',     type: 'text' },
    { key: 'newsapi_interval', label: 'NewsAPI Scan Interval',   value: '30 min',     type: 'text' },
    { key: 'dedup_ttl',       label: 'Dedup TTL',               value: '7 days',     type: 'text' },
  ]},
  { section: 'Features', items: [
    { key: 'realtime_ws',    label: 'WebSocket Real-time',      value: true,   type: 'toggle' },
    { key: 'auto_pipeline',  label: 'Auto Pipeline Trigger',    value: true,   type: 'toggle' },
    { key: 'risk_gate',      label: 'Risk Gate Enforcement',    value: true,   type: 'toggle' },
    { key: 'debug_logs',     label: 'Debug Logging',            value: false,  type: 'toggle' },
  ]},
]

export default function AdminSettings() {
  const [toggles, setToggles] = useState(() => {
    const t = {}
    SETTINGS.forEach(s => s.items.forEach(i => {
      if (i.type === 'toggle') t[i.key] = i.value
    }))
    return t
  })

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-sm uppercase tracking-[0.5em] font-light">Settings</h1>
        <div className="h-px w-8 bg-red-600 mt-2" />
      </div>

      {SETTINGS.map(section => (
        <div key={section.section} className="glass-panel p-5">
          <div className="panel-accent" />
          <div className="text-[9px] uppercase tracking-[0.4em] text-gray-500 mb-4">{section.section}</div>
          <div className="space-y-4">
            {section.items.map(item => (
              <div key={item.key} className="flex items-center justify-between py-2 border-b border-white/[0.03] last:border-0">
                <div className="text-[11px] tracking-wide font-light">{item.label}</div>
                {item.masked ? (
                  <div className="flex items-center gap-2">
                    <span className="text-[11px] monospaced text-gray-500">{item.value}</span>
                    <button className="text-[9px] uppercase tracking-[0.2em] text-gray-600 hover:text-red-500 transition-colors">
                      Reveal
                    </button>
                  </div>
                ) : item.type === 'toggle' ? (
                  <button
                    onClick={() => setToggles(t => ({ ...t, [item.key]: !t[item.key] }))}
                    className={`w-10 h-5 rounded-full relative transition-colors ${toggles[item.key] ? 'bg-red-600/40' : 'bg-white/10'}`}
                  >
                    <div className={`absolute top-0.5 w-4 h-4 rounded-full transition-all ${toggles[item.key] ? 'left-5 bg-red-500' : 'left-0.5 bg-gray-500'}`} />
                  </button>
                ) : (
                  <input
                    type="text"
                    defaultValue={item.value}
                    className="bg-transparent border border-white/10 rounded px-3 py-1 text-[11px] tracking-wide w-32 text-right focus:outline-none focus:border-red-600/50 transition-colors"
                  />
                )}
              </div>
            ))}
          </div>
        </div>
      ))}

      {/* Danger zone */}
      <div className="glass-panel p-5 border-red-600/20">
        <div className="panel-accent" />
        <div className="text-[9px] uppercase tracking-[0.4em] text-red-500 mb-4">Danger Zone</div>
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-[11px] tracking-wide font-light">Purge All Events</div>
              <div className="text-[9px] text-gray-600">Remove all ingested events from the database</div>
            </div>
            <button className="px-3 py-1.5 text-[9px] uppercase tracking-[0.2em] border border-red-600/30 text-red-500 rounded hover:bg-red-600/10 transition-colors">
              Purge
            </button>
          </div>
          <div className="flex items-center justify-between">
            <div>
              <div className="text-[11px] tracking-wide font-light">Reset Pipeline State</div>
              <div className="text-[9px] text-gray-600">Clear all queued tasks and reset counters</div>
            </div>
            <button className="px-3 py-1.5 text-[9px] uppercase tracking-[0.2em] border border-red-600/30 text-red-500 rounded hover:bg-red-600/10 transition-colors">
              Reset
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
