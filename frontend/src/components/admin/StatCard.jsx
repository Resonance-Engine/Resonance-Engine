export default function StatCard({ label, value, sub, accent = false }) {
  return (
    <div className="glass-panel p-5 group">
      <div className="panel-accent" />
      <div className="text-[9px] uppercase tracking-[0.4em] text-gray-500 mb-3">{label}</div>
      <div className={`text-2xl font-light tracking-wide ${accent ? 'value-critical' : 'text-white'}`}>
        {value}
      </div>
      {sub && <div className="text-[10px] text-gray-600 mt-1 tracking-wide">{sub}</div>}
    </div>
  )
}
