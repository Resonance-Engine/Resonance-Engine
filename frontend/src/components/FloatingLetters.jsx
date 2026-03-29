import { useEffect, useRef } from 'react'

const CHARS = [
  // Letters from RESONANCE ENGINE
  'R','E','S','O','N','A','C','G','I',
  // Signal / wave / resonance symbols
  'α','β','~','∂','∇','∞','Σ','λ','μ','π',
  // Previous full set (commented out):
  // 'α','β','Δ','Σ','∂','π','λ','μ','∇','∞','%','$','¥','#','0','1',
  // 'A','B','C','D','E','F','G','H','I','J','K','L','M','N','R','S','T','X','Z',
]

// ── Trail mode (true snake — each letter follows the head's path) ─

const HIST = 1500  // enough frames to cover full snake length at any refresh rate

const SEED_WORDS = ['RESONANCE', 'ENGINE']

function createStream(idx) {
  // All streams start clustered in the top-left corner area
  const offset = idx * 32
  const onTop  = idx % 2 === 0
  const sx     = onTop ? offset : 0
  const sy     = onTop ? 0 : offset

  // All streams travel at exactly 45° down-right
  const angle   = Math.PI * 0.25
  const speed   = 1.0 + Math.random() * 0.8          // 1.0 – 1.8
  const trail   = 28 + Math.floor(Math.random() * 24) // 28 – 51 letters
  const spacing = 14

  // First two snakes spell out a word from head→tail, then flip away naturally
  const word = idx < SEED_WORDS.length ? SEED_WORDS[idx] : null

  // Pre-fill history at the start position so tail doesn't flash in
  const history = Array.from({ length: HIST }, () => ({ x: sx, y: sy }))

  return {
    x:          sx,
    y:          sy,
    vx:         Math.cos(angle) * speed,
    vy:         Math.sin(angle) * speed,
    trail,
    spacing,
    history,
    chars:      Array.from({ length: trail }, (_, li) => ({
      char:      word && li < word.length
                   ? word[li]
                   : CHARS[Math.floor(Math.random() * CHARS.length)],
      flipMs:    word && li < word.length ? 0 : Math.random() * 1500,
      flipEvery: 900 + Math.random() * 800,   // 0.9 – 1.7 s, then flips away
    })),
    size:       13,
    opacity:    0.28 + Math.random() * 0.38,
    bounces:    0,
    maxBounces: 3 + Math.floor(Math.random() * 6),
  }
}

// ── Drift mode (original random floaters for login screen) ────

const BASE_ANGLES = [
  Math.PI * 0.25, Math.PI * 0.75, Math.PI * 1.25, Math.PI * 1.75,
]

function createDrifter(w, h) {
  const angle = BASE_ANGLES[Math.floor(Math.random() * 4)] + (Math.random() - 0.5) * 0.25
  const speed = 0.7 + Math.random() * 0.9
  return {
    x:          Math.random() * w,
    y:          Math.random() * h,
    vx:         Math.cos(angle) * speed,
    vy:         Math.sin(angle) * speed,
    char:       CHARS[Math.floor(Math.random() * CHARS.length)],
    flipMs:     0,
    flipEvery:  500 + Math.random() * 500,   // ms between flips
    size:       11 + Math.random() * 9,
    opacity:    0.25 + Math.random() * 0.3,
    bounces:    0,
    maxBounces: 2 + Math.floor(Math.random() * 5),
  }
}

// ── Component ─────────────────────────────────────────────────

export default function FloatingLetters({ count, mode = 'trail' }) {
  const canvasRef    = useRef(null)
  const containerRef = useRef(null)
  const n = count ?? (mode === 'trail' ? 9 : 35)

  useEffect(() => {
    const canvas    = canvasRef.current
    const container = containerRef.current
    if (!canvas || !container) return

    const ctx = canvas.getContext('2d')
    let w = container.clientWidth  || window.innerWidth
    let h = container.clientHeight || window.innerHeight
    canvas.width  = w
    canvas.height = h

    const GRID_SIZE = 48

    const drawGrid = () => {
      ctx.fillStyle = 'rgba(255, 51, 51, 0.03)'
      for (let x = 0; x < w; x += GRID_SIZE) {
        for (let y = 0; y < h; y += GRID_SIZE) {
          ctx.beginPath()
          ctx.arc(x, y, 1, 0, Math.PI * 2)
          ctx.fill()
        }
      }
    }

    let particles
    let animId

    // ── Trail tick ──────────────────────────────────────────────
    if (mode === 'trail') {
      particles = Array.from({ length: n }, (_, i) => createStream(i))

      let lastTime = performance.now()
      const tick = (timestamp) => {
        const dtMs = Math.min(timestamp - lastTime, 50) // ms elapsed, capped at 50ms
        const dt   = dtMs / 16.667                      // normalised to 60fps units
        lastTime   = timestamp

        ctx.clearRect(0, 0, w, h)
        drawGrid()

        for (let si = 0; si < particles.length; si++) {
          const s = particles[si]

          // Move head (dt-scaled so speed is identical at any refresh rate)
          s.x += s.vx * dt
          s.y += s.vy * dt

          // Bounce off walls
          let bounced = false
          if (s.x <= 0)  { s.vx =  Math.abs(s.vx); s.x = 0; bounced = true }
          if (s.x >= w)  { s.vx = -Math.abs(s.vx); s.x = w; bounced = true }
          if (s.y <= 0)  { s.vy =  Math.abs(s.vy); s.y = 0; bounced = true }
          if (s.y >= h)  { s.vy = -Math.abs(s.vy); s.y = h; bounced = true }

          if (bounced) {
            s.bounces++
            if (s.bounces >= s.maxBounces) {
              particles[si] = createStream(si)
              continue
            }
          }

          // Push every frame for smooth sub-pixel positions
          s.history.unshift({ x: s.x, y: s.y })
          if (s.history.length > HIST) s.history.length = HIST

          // Draw each letter at its exact pixel distance along the path (smooth + density-consistent)
          for (let li = 0; li < s.trail; li++) {
            const targetDist = li * s.spacing

            // Walk back through history until we've accumulated targetDist pixels
            let dist = 0
            let pos  = s.history[0]
            for (let hi = 1; hi < s.history.length; hi++) {
              const dx     = s.history[hi - 1].x - s.history[hi].x
              const dy     = s.history[hi - 1].y - s.history[hi].y
              const segLen = Math.sqrt(dx * dx + dy * dy)
              if (dist + segLen >= targetDist) {
                const t = (targetDist - dist) / segLen
                pos = {
                  x: s.history[hi - 1].x + (s.history[hi].x - s.history[hi - 1].x) * t,
                  y: s.history[hi - 1].y + (s.history[hi].y - s.history[hi - 1].y) * t,
                }
                break
              }
              dist += segLen
              if (hi === s.history.length - 1) pos = s.history[hi] // end of recorded path
            }

            const c = s.chars[li]
            c.flipMs += dtMs
            if (c.flipMs >= c.flipEvery) {
              c.flipMs -= c.flipEvery
              c.char = CHARS[Math.floor(Math.random() * CHARS.length)]
            }

            const fade    = 1 - (li / s.trail) * 0.78
            ctx.font      = `300 ${s.size}px monospace`
            ctx.fillStyle = `rgba(255, 51, 51, ${s.opacity * fade})`
            ctx.fillText(c.char, pos.x, pos.y)
          }
        }

        animId = requestAnimationFrame(tick)
      }
      tick(performance.now())

    // ── Drift tick ─────────────────────────────────────────────
    } else {
      particles = Array.from({ length: n }, () => createDrifter(w, h))

      let lastTime = performance.now()
      const tick = (timestamp) => {
        const dtMs = Math.min(timestamp - lastTime, 50)
        const dt   = dtMs / 16.667
        lastTime   = timestamp

        ctx.clearRect(0, 0, w, h)

        for (let i = 0; i < particles.length; i++) {
          const p = particles[i]
          p.x += p.vx * dt
          p.y += p.vy * dt

          let bounced = false
          if (p.x <= 0 || p.x >= w) { p.vx *= -1; p.x = Math.max(0, Math.min(w, p.x)); bounced = true }
          if (p.y <= 0 || p.y >= h) { p.vy *= -1; p.y = Math.max(0, Math.min(h, p.y)); bounced = true }
          if (bounced) {
            p.bounces++
            if (p.bounces >= p.maxBounces) { particles[i] = createDrifter(w, h); continue }
          }

          p.flipMs += dtMs
          if (p.flipMs >= p.flipEvery) {
            p.flipMs -= p.flipEvery
            p.char = CHARS[Math.floor(Math.random() * CHARS.length)]
          }

          ctx.font      = `300 ${p.size}px monospace`
          ctx.fillStyle = `rgba(255, 51, 51, ${p.opacity})`
          ctx.fillText(p.char, p.x, p.y)
        }

        animId = requestAnimationFrame(tick)
      }
      tick(performance.now())
    }

    const onResize = () => {
      w = container.clientWidth  || window.innerWidth
      h = container.clientHeight || window.innerHeight
      canvas.width  = w
      canvas.height = h
      if (mode === 'trail') {
        particles.splice(0, particles.length, ...Array.from({ length: n }, (_, i) => createStream(i)))
      } else {
        particles.splice(0, particles.length, ...Array.from({ length: n }, () => createDrifter(w, h)))
      }
    }
    window.addEventListener('resize', onResize)

    return () => {
      cancelAnimationFrame(animId)
      window.removeEventListener('resize', onResize)
    }
  }, [n, mode])

  return (
    <div ref={containerRef} className="absolute inset-0 pointer-events-none overflow-hidden" aria-hidden="true">
      <canvas ref={canvasRef} className="absolute inset-0" />
    </div>
  )
}
