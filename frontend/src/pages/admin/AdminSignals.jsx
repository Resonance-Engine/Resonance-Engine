import { useState } from 'react'
import DataTable from '../../components/admin/DataTable'
import StatusBadge from '../../components/admin/StatusBadge'
import { mockSignals } from '../../data/mockAdmin'

export default function AdminSignals() {
  const [filter, setFilter] = useState('all')

  const filtered = filter === 'all'
    ? mockSignals
    : mockSignals.filter(s => s.status === filter)

  const columns = [
    { key: 'ticker',     label: 'Ticker',     render: (v) => <span className="text-red-500 font-medium">{v}</span> },
    { key: 'type',       label: 'Type',       render: (v) => <span className="text-gray-400">{v.replace(/_/g, ' ')}</span> },
    { key: 'confidence', label: 'Confidence',  render: (v) => (
      <div className="flex items-center gap-2">
        <div className="w-16 h-1 bg-white/10 rounded overflow-hidden">
          <div className="h-full bg-red-600 rounded" style={{ width: `${v * 100}%` }} />
        </div>
        <span className="monospaced text-gray-400">{(v * 100).toFixed(0)}%</span>
      </div>
    )},
    { key: 'impact',     label: 'Window' },
    { key: 'status',     label: 'Status',     render: (v) => <StatusBadge status={v} /> },
    { key: 'timestamp',  label: 'Time',       render: (v) => new Date(v).toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit' }) },
    { key: 'actions',    label: '',            sortable: false, render: () => (
      <button className="text-[9px] uppercase tracking-[0.2em] text-gray-600 hover:text-red-500 transition-colors">
        Delete
      </button>
    )},
  ]

  return (
    <div className="space-y-6">
      <div className="flex items-end justify-between">
        <div>
          <h1 className="text-sm uppercase tracking-[0.5em] font-light">Signal Browser</h1>
          <div className="h-px w-8 bg-red-600 mt-2" />
        </div>
        <div className="flex gap-2">
          {['all', 'active', 'pending', 'expired'].map(f => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-3 py-1 text-[9px] uppercase tracking-[0.2em] border rounded transition-colors ${
                filter === f
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
