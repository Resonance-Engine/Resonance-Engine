const STYLES = {
  active:    'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
  running:   'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
  completed: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
  processed: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
  idle:      'bg-gray-500/20 text-gray-400 border-gray-500/30',
  inactive:  'bg-gray-500/20 text-gray-400 border-gray-500/30',
  pending:   'bg-amber-500/20 text-amber-400 border-amber-500/30',
  suspended: 'bg-red-500/20 text-red-400 border-red-500/30',
  error:     'bg-red-500/20 text-red-400 border-red-500/30',
  failed:    'bg-red-500/20 text-red-400 border-red-500/30',
  expired:   'bg-gray-500/20 text-gray-500 border-gray-500/30',
  admin:     'bg-red-500/20 text-red-400 border-red-500/30',
  user:      'bg-blue-500/20 text-blue-400 border-blue-500/30',
}

export default function StatusBadge({ status }) {
  const style = STYLES[status] || STYLES.idle
  return (
    <span className={`inline-block px-2 py-0.5 text-[9px] uppercase tracking-[0.2em] border rounded ${style}`}>
      {status}
    </span>
  )
}
