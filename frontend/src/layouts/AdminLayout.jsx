import { NavLink, Outlet, Link } from 'react-router-dom'
import NoiseOverlay from '../components/NoiseOverlay'

const NAV_ITEMS = [
  { to: '/admin',          label: 'Dashboard',  icon: '◆' },
  { to: '/admin/users',    label: 'Users',      icon: '◎' },
  { to: '/admin/signals',  label: 'Signals',    icon: '⚡' },
  { to: '/admin/events',   label: 'Events',     icon: '◈' },
  { to: '/admin/pipeline', label: 'Pipeline',   icon: '▶' },
  { to: '/admin/settings', label: 'Settings',   icon: '⚙' },
]

export default function AdminLayout() {
  return (
    <div className="flex min-h-screen">
      <NoiseOverlay />

      {/* Sidebar */}
      <aside className="w-56 flex-shrink-0 border-r border-white/5 bg-[#080808] flex flex-col fixed h-full z-40">
        {/* Logo */}
        <Link to="/" className="px-5 py-4 border-b border-white/5 group flex items-center gap-3">
          <img src="/logo.svg" alt="Resonance Engine" className="h-7 transition-opacity group-hover:opacity-80" />
          <div className="text-[8px] uppercase tracking-[0.3em] text-gray-600">Admin</div>
        </Link>

        {/* Navigation */}
        <nav className="flex-1 py-4 px-3 space-y-1">
          {NAV_ITEMS.map(item => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/admin'}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded text-[10px] uppercase tracking-[0.3em] transition-all ${
                  isActive
                    ? 'bg-red-600/10 text-red-500 border border-red-600/20'
                    : 'text-gray-500 hover:text-gray-300 hover:bg-white/[0.02] border border-transparent'
                }`
              }
            >
              <span className="text-xs">{item.icon}</span>
              {item.label}
            </NavLink>
          ))}
        </nav>

        {/* Sidebar footer */}
        <div className="px-5 py-4 border-t border-white/5">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse" />
            <span className="text-[9px] uppercase tracking-[0.2em] text-gray-600">System Online</span>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 ml-56">
        {/* Top bar */}
        <header className="sticky top-0 z-30 h-12 border-b border-white/5 bg-[#0a0a0a]/90 backdrop-blur-md flex items-center justify-between px-6">
          <div className="text-[9px] uppercase tracking-[0.4em] text-gray-600">
            Admin Console
          </div>
          <div className="flex items-center gap-4">
            <Link to="/dashboard" className="text-[9px] uppercase tracking-[0.3em] text-gray-600 hover:text-red-500 transition-colors">
              Exit Admin →
            </Link>
          </div>
        </header>

        {/* Page content */}
        <div className="p-6">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
