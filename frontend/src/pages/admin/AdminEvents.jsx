import { useState } from 'react'
import DataTable from '../../components/admin/DataTable'
import StatusBadge from '../../components/admin/StatusBadge'
import { mockEvents } from '../../data/mockAdmin'

export default function AdminEvents() {
  const [sourceFilter, setSourceFilter] = useState('all')

  const filtered = sourceFilter === 'all'
    ? mockEvents
    : mockEvents.filter(e => e.source === sourceFilter)

  const columns = [
    { key: 'source',    label: 'Source',   render: (v) => (
      <span className={`text-[10px] font-medium tracking-wide ${
        v === 'EDGAR' ? 'text-blue-400' : v === 'NewsAPI' ? 'text-amber-400' : 'text-emerald-400'
      }`}>{v}</span>
    )},
    { key: 'type',      label: 'Type',     render: (v) => <span className="text-gray-400">{v}</span> },
    { key: 'entities',  label: 'Entities', render: (v) => (
      <div className="flex gap-1">
        {v.map(e => (
          <span key={e} className="px-1.5 py-0.5 text-[9px] bg-white/5 border border-white/10 rounded text-red-400">{e}</span>
        ))}
      </div>
    )},
    { key: 'status',    label: 'Status',   render: (v) => <StatusBadge status={v} /> },
    { key: 'timestamp', label: 'Time',     render: (v) => new Date(v).toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit' }) },
  ]

  return (
    <div className="space-y-6">
      <div className="flex items-end justify-between">
        <div>
          <h1 className="text-sm uppercase tracking-[0.5em] font-light">Event Browser</h1>
          <div className="h-px w-8 bg-red-600 mt-2" />
        </div>
        <div className="flex gap-2">
          {['all', 'EDGAR', 'NewsAPI', 'GDELT'].map(f => (
            <button
              key={f}
              onClick={() => setSourceFilter(f)}
              className={`px-3 py-1 text-[9px] uppercase tracking-[0.2em] border rounded transition-colors ${
                sourceFilter === f
                  ? 'border-red-600/50 text-red-500 bg-red-600/10'
                  : 'border-white/10 text-gray-600 hover:text-gray-400'
              }`}
            >
              {f}
            </button>
          ))}
        </div>
      </div>

      <DataTable
        columns={columns}
        data={filtered}
        expandable={(row) => (
          <div className="text-[11px] text-gray-400 font-light tracking-wide leading-relaxed">
            <span className="text-[9px] uppercase tracking-[0.3em] text-gray-600 block mb-1">Summary</span>
            {row.summary}
          </div>
        )}
      />
    </div>
  )
}
