import { useState, useEffect, useRef } from 'react'

function mapRange(value, inMin, inMax) {
  return Math.min(1, Math.max(0, (value - inMin) / (inMax - inMin)))
}

export default function LogoIntro() {
  const containerRef = useRef(null)
  const [progress, setProgress] = useState(0)

  const outerRef = useRef(null)
  const innerRef = useRef(null)
  const horizRef = useRef(null)
  const vertRef  = useRef(null)
  const [lengths, setLengths] = useState({ outer: 396, inner: 328, horiz: 145, vert: 145 })

  // Measure actual path lengths after mount
  useEffect(() => {
    if (outerRef.current) {
      setLengths({
        outer: outerRef.current.getTotalLength(),
        inner: innerRef.current.getTotalLength(),
        horiz: horizRef.current.getTotalLength(),
        vert:  vertRef.current.getTotalLength(),
      })
    }
  }, [])

  // Drive progress from scroll position within the container
  useEffect(() => {
    const handleScroll = () => {
      if (!containerRef.current) return
      const rect = containerRef.current.getBoundingClientRect()
      const totalScrollable = containerRef.current.offsetHeight - window.innerHeight
      const scrolled = -rect.top
      setProgress(Math.min(1, Math.max(0, scrolled / totalScrollable)))
    }
    window.addEventListener('scroll', handleScroll, { passive: true })
    handleScroll() // set on mount in case page is pre-scrolled
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  // Per-element animation progress (inside-out draw order)
  const coreOpacity    = mapRange(progress, 0.00, 0.15)
  const nodesOpacity   = mapRange(progress, 0.10, 0.25)
  const wavesP         = mapRange(progress, 0.20, 0.55)
  const innerP         = mapRange(progress, 0.50, 0.80)
  const outerP         = mapRange(progress, 0.75, 1.00)
  const particlesAlpha = mapRange(progress, 0.60, 1.00)

  const horizOffset = lengths.horiz * (1 - wavesP)
  const vertOffset  = lengths.vert  * (1 - wavesP)
  const innerOffset = lengths.inner * (1 - innerP)
  const outerOffset = lengths.outer * (1 - outerP)

  return (
    // Tall scroll track — sticky child pins to viewport while scrolling through it
    <div ref={containerRef} className="relative h-[280vh]">
      <div
        className="sticky top-0 h-screen flex items-center justify-center overflow-hidden"
        style={{ background: '#0a0a0a', cursor: 'crosshair' }}
      >
        {/* Red radial glow — builds with progress */}
        <div
          className="absolute inset-0 pointer-events-none"
          style={{
            background: 'radial-gradient(circle at center, rgba(255,51,51,0.14) 0%, rgba(255,51,51,0.05) 40%, transparent 70%)',
            opacity: progress,
          }}
        />

        <svg
          width="440"
          height="440"
          viewBox="0 0 400 400"
          xmlns="http://www.w3.org/2000/svg"
        >
          <defs>
            <linearGradient id="re-lf" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%"   stopColor="#ff0000" stopOpacity="0.3" />
              <stop offset="50%"  stopColor="#ff3333" stopOpacity="1" />
              <stop offset="100%" stopColor="#ff0000" stopOpacity="0.3" />
            </linearGradient>
            <filter id="re-glow">
              <feGaussianBlur stdDeviation="3" result="coloredBlur" />
              <feMerge>
                <feMergeNode in="coloredBlur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
            <filter id="re-sglow">
              <feGaussianBlur stdDeviation="5" result="coloredBlur" />
              <feMerge>
                <feMergeNode in="coloredBlur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
          </defs>

          {/* Ambient background glow */}
          <circle cx="200" cy="200" r="140" fill="rgba(255,51,51,0.08)" opacity={particlesAlpha} />

          {/* Particles + connection lines */}
          <g opacity={particlesAlpha}>
            <circle cx="228" cy="158" r="2"   fill="#ff3333" opacity="0.8"/>
            <circle cx="152" cy="178" r="1.8" fill="#ff3333" opacity="0.75"/>
            <circle cx="242" cy="238" r="1.9" fill="#ff3333" opacity="0.7"/>
            <circle cx="168" cy="268" r="1.7" fill="#ff3333" opacity="0.65"/>
            <circle cx="270" cy="138" r="1.5" fill="#ff3333" opacity="0.6"/>
            <circle cx="118" cy="168" r="1.4" fill="#ff3333" opacity="0.55"/>
            <circle cx="282" cy="278" r="1.6" fill="#ff3333" opacity="0.6"/>
            <circle cx="130" cy="308" r="1.4" fill="#ff3333" opacity="0.5"/>
            <circle cx="302" cy="118" r="1.2" fill="#ff3333" opacity="0.45"/>
            <circle cx="88"  cy="148" r="1.1" fill="#ff3333" opacity="0.4"/>
            <circle cx="315" cy="305" r="1.2" fill="#ff3333" opacity="0.45"/>
            <circle cx="248" cy="105" r="1.1" fill="#ff3333" opacity="0.5"/>
            <circle cx="297" cy="218" r="1"   fill="#ff3333" opacity="0.45"/>
            <circle cx="188" cy="325" r="1.2" fill="#ff3333" opacity="0.5"/>
            <circle cx="102" cy="238" r="1"   fill="#ff3333" opacity="0.4"/>
            <circle cx="155" cy="95"  r="1.1" fill="#ff3333" opacity="0.45"/>
            <line x1="228" y1="158" x2="200" y2="145" stroke="#ff3333" strokeWidth="0.6" opacity="0.15"/>
            <line x1="270" y1="138" x2="248" y2="105" stroke="#ff3333" strokeWidth="0.6" opacity="0.1"/>
            <line x1="242" y1="238" x2="200" y2="255" stroke="#ff3333" strokeWidth="0.6" opacity="0.15"/>
            <line x1="282" y1="278" x2="315" y2="305" stroke="#ff3333" strokeWidth="0.6" opacity="0.1"/>
            <line x1="152" y1="178" x2="118" y2="168" stroke="#ff3333" strokeWidth="0.6" opacity="0.12"/>
            <line x1="168" y1="268" x2="130" y2="308" stroke="#ff3333" strokeWidth="0.6" opacity="0.12"/>
          </g>

          <g transform="translate(200, 200)">

            {/* Ghost outlines — always visible skeleton */}
            <path d="M -70 0 Q -35 -15, 0 0 T 70 0"  fill="none" stroke="#ff3333" strokeWidth="1.5" opacity="0.22" />
            <path d="M 0 -70 Q 15 -35, 0 0 T 0 70"    fill="none" stroke="#ff3333" strokeWidth="1.5" opacity="0.16" />
            <path d="M 0 -58 L 58 0 L 0 58 L -58 0 Z" fill="none" stroke="#ff3333" strokeWidth="1.5" opacity="0.20" />
            <path d="M 0 -70 L 70 0 L 0 70 L -70 0 Z" fill="none" stroke="#ffffff" strokeWidth="1"   opacity="0.10" />
            <circle cx="0"   cy="-58" r="2.5" fill="none" stroke="#ff3333" strokeWidth="1.5" opacity="0.22" />
            <circle cx="58"  cy="0"   r="2.5" fill="none" stroke="#ff3333" strokeWidth="1.5" opacity="0.22" />
            <circle cx="0"   cy="58"  r="2.5" fill="none" stroke="#ff3333" strokeWidth="1.5" opacity="0.22" />
            <circle cx="-58" cy="0"   r="2.5" fill="none" stroke="#ff3333" strokeWidth="1.5" opacity="0.22" />

            {/* 1 — Center core */}
            <g opacity={coreOpacity}>
              <circle cx="0" cy="0" r="8"   fill="#1a1a1a"/>
              <circle cx="0" cy="0" r="5.5" fill="#ff3333" filter="url(#re-sglow)"/>
              <circle cx="0" cy="0" r="3"   fill="#ff0000"/>
              <circle cx="0" cy="0" r="1.5" fill="#ffffff"/>
            </g>

            {/* 2 — Corner energy nodes */}
            <g opacity={nodesOpacity}>
              <circle cx="0"   cy="-58" r="2.5" fill="#ff3333" opacity="0.8"/>
              <circle cx="58"  cy="0"   r="2.5" fill="#ff3333" opacity="0.8"/>
              <circle cx="0"   cy="58"  r="2.5" fill="#ff3333" opacity="0.8"/>
              <circle cx="-58" cy="0"   r="2.5" fill="#ff3333" opacity="0.8"/>
            </g>

            {/* 3 — Horizontal wave */}
            <path
              ref={horizRef}
              d="M -70 0 Q -35 -15, 0 0 T 70 0"
              fill="none" stroke="url(#re-lf)" strokeWidth="2"
              filter="url(#re-glow)"
              strokeDasharray={lengths.horiz}
              strokeDashoffset={horizOffset}
            />

            {/* 3 — Vertical wave */}
            <path
              ref={vertRef}
              d="M 0 -70 Q 15 -35, 0 0 T 0 70"
              fill="none" stroke="url(#re-lf)" strokeWidth="2" opacity="0.7"
              filter="url(#re-glow)"
              strokeDasharray={lengths.vert}
              strokeDashoffset={vertOffset}
            />

            {/* 4 — Inner diamond */}
            <path
              ref={innerRef}
              d="M 0 -58 L 58 0 L 0 58 L -58 0 Z"
              fill="none" stroke="url(#re-lf)" strokeWidth="2"
              filter="url(#re-glow)"
              strokeDasharray={lengths.inner}
              strokeDashoffset={innerOffset}
            />

            {/* 5 — Outer diamond */}
            <path
              ref={outerRef}
              d="M 0 -70 L 70 0 L 0 70 L -70 0 Z"
              fill="none" stroke="#3a3a3a" strokeWidth="2"
              strokeDasharray={lengths.outer}
              strokeDashoffset={outerOffset}
            />

          </g>
        </svg>

        {/* Scroll hint at the very start */}
        <div
          className="absolute bottom-12 left-1/2 -translate-x-1/2 flex flex-col items-center gap-2 pointer-events-none transition-opacity duration-500"
          style={{ opacity: progress < 0.04 ? 0.4 : 0 }}
        >
          <span className="text-[9px] uppercase tracking-[0.6em] text-white animate-pulse">Scroll</span>
          <div className="w-px h-10 bg-gradient-to-b from-white/30 to-transparent" />
        </div>

        {/* Progress bar — bottom edge */}
        <div
          className="absolute bottom-0 left-0 h-px bg-red-600/50 transition-none"
          style={{ width: `${progress * 100}%` }}
        />
      </div>
    </div>
  )
}
