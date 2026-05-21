import { useState } from 'react'
import StatusBadge from '../../components/admin/StatusBadge'
import DataTable from '../../components/admin/DataTable'
import { mockPipeline } from '../../data/mockAdmin'
import { runPipeline } from '../../api/client'

export default function AdminPipeline() {
  const [sources, setSources] = useState(mockPipeline.sources)
  const [tasks, setTasks] = useState(mockPipeline.recentTasks)
  const [triggeringSource, setTriggeringSource] = useState(null)
  const [logs, setLogs] = useState([
    { time: '14:23:12', level: 'INFO',  color: 'text-emerald-400', msg: 'EDGAR cycle started — scanning 8-K filings' },
    { time: '14:23:14', level: 'INFO',  color: 'text-emerald-400', msg: 'Found 23 new filings since last scan' },
    { time: '14:23:15', level: 'INFO',  color: 'text-emerald-400', msg: 'Dedup: 4 duplicates filtered (content_hash match)' },
    { time: '14:23:15', level: 'INFO',  color: 'text-emerald-400', msg: 'Entity resolution: 19 events → 14 unique tickers' },
    { time: '14:23:16', level: 'DEBUG', color: 'text-blue-400',    msg: 'Pipeline ingested event evt_001 (AAPL, 8-K)' },
    { time: '14:23:16', level: 'INFO',  color: 'text-emerald-400', msg: 'Signal generated: sig_001 (AAPL, earnings_beat, conf=0.92)' },
    { time: '14:23:16', level: 'INFO',  color: 'text-emerald-400', msg: 'EDGAR cycle completed in 4.2s' },
    { time: '14:23:16', level: 'INFO',  color: 'text-gray-500',    msg: 'Next EDGAR scan in 15 min' },
    { time: '14:51:30', level: 'WARN',  color: 'text-amber-400',   msg: 'NewsAPI rate limit approaching (92/100 daily)' },
    { time: '14:51:30', level: 'ERROR', color: 'text-red-400',     msg: 'NewsAPI request failed: 429 Too Many Requests' },
    { time: '14:51:30', level: 'WARN',  color: 'text-amber-400',   msg: 'Retry scheduled in 42s' },
  ])

  const addLog = (level, color, msg) => {
    const now = new Date().toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' })
    setLogs(prev => [{ time: now, level, color, msg }, ...prev].slice(0, 30))
  }

  const handleTrigger = async (sourceName) => {
    setTriggeringSource(sourceName)
    addLog('INFO', 'text-emerald-400', `Manual trigger: ${sourceName} pipeline started`)

    // Update source status to running
    setSources(prev => prev.map(s =>
      s.name === sourceName ? { ...s, status: 'running' } : s
    ))

    try {
      const sampleText = `Manual trigger from admin panel for ${sourceName} pipeline ingestion cycle.`
      const result = await runPipeline(sampleText, { source: sourceName === 'EDGAR' ? 'SEC_EDGAR' : sourceName })

      if (result.signal_id) {
        addLog('INFO', 'text-emerald-400', `${sourceName} pipeline completed — signal ${result.signal_id.substring(0, 8)} generated`)
        setTasks(prev => [{
          id: `tsk_live_${Date.now()}`,
          source: sourceName,
          status: 'completed',
          events: 1,
          duration: '—',
          started: 'just now',
        }, ...prev].slice(0, 10))
      } else if (result.rejection_reason) {
        addLog('WARN', 'text-amber-400', `${sourceName} pipeline: rejected — ${result.rejection_reason}`)
        setTasks(prev => [{
          id: `tsk_live_${Date.now()}`,
          source: sourceName,
          status: 'completed',
          events: 0,
          duration: '—',
          started: 'just now',
        }, ...prev].slice(0, 10))
      }
    } catch (err) {
      addLog('ERROR', 'text-red-400', `${sourceName} trigger failed: ${err.message}`)
      setTasks(prev => [{
        id: `tsk_live_${Date.now()}`,
        source: sourceName,
        status: 'failed',
        events: 0,
        duration: '—',
        started: 'just now',
        error: err.message,
      }, ...prev].slice(0, 10))
    } finally {
      setSources(prev => prev.map(s =>
        s.name === sourceName ? { ...s, status: 'idle', lastRun: 'just now' } : s
      ))
      setTriggeringSource(null)
    }
  }

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
        {sources.map(src => (
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
              <button
                onClick={() => handleTrigger(src.name)}
                disabled={triggeringSource === src.name}
                className={`px-3 py-1 text-[9px] uppercase tracking-[0.2em] border border-red-600/30 text-red-500 rounded hover:bg-red-600/10 transition-colors ${triggeringSource === src.name ? 'opacity-50 cursor-wait' : ''}`}
              >
                {triggeringSource === src.name ? 'Running...' : 'Trigger'}
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
          data={tasks}
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
          {logs.map((log, i) => (
            <div key={i} className="text-gray-600">
              [{log.time}] <span className={log.color}>{log.level.padEnd(5)}</span> {log.msg}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
