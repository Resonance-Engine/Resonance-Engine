export default function GlassPanel({ children, className = '', style }) {
  return (
    <div className={`glass-panel ${className}`} style={style}>
      {children}
    </div>
  )
}
