import StatCard from '../../components/admin/StatCard'
import StatusBadge from '../../components/admin/StatusBadge'
import { adminStats, recentActivity, mockPipeline } from '../../data/mockAdmin'

const ACTIVITY_ICONS = {
  signal: '⚡', user: '◎', pipeline: '▶', error: '✕',
}

export default function AdminDashboard() {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-sm uppercase tracking-[0.5em] font-light">Dashboard</h1>
        <div className="h-px w-8 bg-red-600 mt-2" />
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="Total Users"      value={adminStats.totalUsers.toLocaleString()} sub="+12 this week" />
        <StatCard label="Active Signals"   value={adminStats.activeSignals} sub={`${adminStats.signalsGenerated24h} generated (24h)`} accent />
        <StatCard label="Events Today"     value={adminStats.eventsToday} sub="3 sources active" />
        <StatCard label="Pipeline Health"  value={`${adminStats.pipelineHealth}%`} sub={`Avg confidence: ${adminStats.avgConfidence}`} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Pipeline sources status */}
        <div className="glass-panel p-5 lg:col-span-1">
          <div className="text-[9px] uppercase tracking-[0.4em] text-gray-500 mb-4">Pipeline Sources</div>
          <div className="space-y-3">
            {mockPipeline.sources.map(src => (
              <div key={src.name} className="flex items-center justify-between py-2 border-b border-white/[0.03] last:border-0">
                <div className="flex items-center gap-3">
                  <StatusBadge status={src.status} />
                  <span className="text-[11px] tracking-wide">{src.name}</span>
                </div>
                <div className="text-right">
                  <div className="text-[10px] text-gray-400">{src.eventsToday} events</div>
                  <div className="text-[9px] text-gray-600">next: {src.nextRun}</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Recent activity */}
        <div className="glass-panel p-5 lg:col-span-2">
          <div className="text-[9px] uppercase tracking-[0.4em] text-gray-500 mb-4">Recent Activity</div>
          <div className="space-y-0">
            {recentActivity.map(item => (
              <div key={item.id} className="flex items-start gap-3 py-2.5 border-b border-white/[0.03] last:border-0">
                <span className={`text-xs mt-0.5 ${item.type === 'error' ? 'text-red-500' : 'text-gray-600'}`}>
                  {ACTIVITY_ICONS[item.type]}
                </span>
                <div className="flex-1 min-w-0">
                  <div className="text-[11px] font-light tracking-wide truncate">{item.message}</div>
                </div>
                <div className="text-[9px] text-gray-600 whitespace-nowrap">{item.time}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Signal volume chart placeholder */}
      <div className="glass-panel p-5">
        <div className="text-[9px] uppercase tracking-[0.4em] text-gray-500 mb-4">Signal Volume (24h)</div>
        <div className="h-32 flex items-end gap-1">
          {Array.from({ length: 24 }, (_, i) => {
            const h = 15 + Math.random() * 85
            const isNow = i === 23
            return (
              <div key={i} className="flex-1 flex flex-col items-center gap-1">
                <div
                  className={`w-full rounded-sm transition-all ${isNow ? 'bg-red-600' : 'bg-red-600/20 hover:bg-red-600/40'}`}
                  style={{ height: `${h}%` }}
                />
                {i % 4 === 0 && (
                  <span className="text-[8px] text-gray-700">{`${i}:00`}</span>
                )}
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
