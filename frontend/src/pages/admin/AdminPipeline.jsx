import StatCard from '../../components/admin/StatCard'
import StatusBadge from '../../components/admin/StatusBadge'
import DataTable from '../../components/admin/DataTable'
import { mockPipeline } from '../../data/mockAdmin'

export default function AdminPipeline() {
  const columns = [
    { key: 'source',   label: 'Source' },
    { key: 'status',   label: 'Status',   render: (v) => <StatusBadge status={v} /> },
    { key: 'events',   label: 'Events',   render: (v) => <span className="monospaced">{v}</span> },
    { key: 'duration', label: 'Duration', render: (v) => <span className="monospaced text-gray-400">{v}</span> },
    { key: 'started',  label: 'Started' },
  ]

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-sm uppercase tracking-[0.5em] font-light">Pipeline Control</h1>
        <div className="h-px w-8 bg-red-600 mt-2" />
      </div>

      {/* Source cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {mockPipeline.sources.map(src => (
          <div key={src.name} className="glass-panel p-5">
            <div className="panel-accent" />
            <div className="flex items-center justify-between mb-4">
              <div className="text-[11px] tracking-wide font-light">{src.name}</div>
              <StatusBadge status={src.status} />
            </div>
            <div className="grid grid-cols-2 gap-3 mb-4">
              <div>
                <div className="text-[9px] uppercase tracking-[0.3em] text-gray-600">Events Today</div>
                <div className="text-lg font-light">{src.eventsToday}</div>
              </div>
              <div>
                <div className="text-[9px] uppercase tracking-[0.3em] text-gray-600">Errors</div>
                <div className={`text-lg font-light ${src.errors > 0 ? 'text-red-500' : 'text-emerald-400'}`}>{src.errors}</div>
              </div>
            </div>
            <div className="flex items-center justify-between pt-3 border-t border-white/5">
              <div className="text-[9px] text-gray-600">Last: {src.lastRun} | Next: {src.nextRun}</div>
              <button className="px-3 py-1 text-[9px] uppercase tracking-[0.2em] border border-red-600/30 text-red-500 rounded hover:bg-red-600/10 transition-colors">
                Trigger
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Task history */}
      <div>
        <div className="text-[9px] uppercase tracking-[0.4em] text-gray-500 mb-3">Task History</div>
        <DataTable
          columns={columns}
          data={mockPipeline.recentTasks}
          expandable={(row) => row.error ? (
            <div className="text-[11px] text-red-400 font-light tracking-wide">
              <span className="text-[9px] uppercase tracking-[0.3em] text-gray-600 block mb-1">Error</span>
              {row.error}
            </div>
          ) : null}
        />
      </div>

      {/* Log viewer */}
      <div className="glass-panel p-5">
        <div className="text-[9px] uppercase tracking-[0.4em] text-gray-500 mb-3">Live Log</div>
        <div className="bg-black/40 rounded p-4 h-48 overflow-y-auto font-mono text-[10px] leading-relaxed space-y-1">
          <div className="text-gray-600">[14:23:12] <span className="text-emerald-400">INFO</span>  EDGAR cycle started — scanning 8-K filings</div>
          <div className="text-gray-600">[14:23:14] <span className="text-emerald-400">INFO</span>  Found 23 new filings since last scan</div>
          <div className="text-gray-600">[14:23:15] <span className="text-emerald-400">INFO</span>  Dedup: 4 duplicates filtered (content_hash match)</div>
          <div className="text-gray-600">[14:23:15] <span className="text-emerald-400">INFO</span>  Entity resolution: 19 events → 14 unique tickers</div>
          <div className="text-gray-600">[14:23:16] <span className="text-blue-400">DEBUG</span> Pipeline ingested event evt_001 (AAPL, 8-K)</div>
          <div className="text-gray-600">[14:23:16] <span className="text-emerald-400">INFO</span>  Signal generated: sig_001 (AAPL, earnings_beat, conf=0.92)</div>
          <div className="text-gray-600">[14:23:16] <span className="text-emerald-400">INFO</span>  EDGAR cycle completed in 4.2s</div>
          <div className="text-gray-600">[14:23:16] <span className="text-gray-500">INFO</span>  Next EDGAR scan in 15 min</div>
          <div className="text-gray-600">[14:51:30] <span className="text-amber-400">WARN</span>  NewsAPI rate limit approaching (92/100 daily)</div>
          <div className="text-gray-600">[14:51:30] <span className="text-red-400">ERROR</span> NewsAPI request failed: 429 Too Many Requests</div>
          <div className="text-gray-600">[14:51:30] <span className="text-amber-400">WARN</span>  Retry scheduled in 42s</div>
        </div>
      </div>
    </div>
  )
}
