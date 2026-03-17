import { Link, useNavigate } from 'react-router-dom'

export default function Navbar() {
  const navigate = useNavigate()

  return (
    <nav className="fixed top-0 left-0 w-full z-[110] border-b border-white/10 overflow-hidden">
      {/* Video background */}
      <video
        className="absolute inset-0 w-full h-full object-cover pointer-events-none"
        style={{ opacity: 0.50 }}
        src="/bg.mp4"
        autoPlay
        loop
        muted
        playsInline
      />
      <div className="relative flex items-center justify-between px-8 py-4">

        {/* Logo */}
        <Link to="/" className="flex items-center gap-3 group">
          <div className="w-7 h-7 border border-red-600 flex items-center justify-center rotate-45 transition-all group-hover:bg-red-600/10 group-hover:shadow-[0_0_15px_rgba(255,51,51,0.3)]">
            <span className="text-[9px] font-black -rotate-45 text-white">RE</span>
          </div>
          <div>
            <div className="text-[11px] font-black tracking-[0.3em] uppercase">Resonance Engine</div>
            <div className="text-[8px] text-red-600 tracking-[0.4em] uppercase opacity-70">Intelligence Platform</div>
          </div>
        </Link>

        {/* Nav Links */}
        <div className="flex items-center gap-8">
          <button
            onClick={() => navigate('/', { state: { skipIntro: true } })}
            className="text-[10px] uppercase tracking-[0.4em] text-gray-400 hover:text-white transition-colors duration-300"
          >
            Home
          </button>
          <Link
            to="/about"
            className="text-[10px] uppercase tracking-[0.4em] text-gray-400 hover:text-white transition-colors duration-300"
          >
            About
          </Link>

          <button
            onClick={() => navigate('/login')}
            className="btn-ignition px-6 py-2 text-[9px] tracking-[0.5em]"
          >
            Login
          </button>
        </div>
      </div>
    </nav>
  )
}
