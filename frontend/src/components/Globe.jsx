import { useEffect, useRef } from 'react'
import * as THREE from 'three'
import { feature } from 'topojson-client'
import { EffectComposer } from 'three/examples/jsm/postprocessing/EffectComposer.js'
import { RenderPass } from 'three/examples/jsm/postprocessing/RenderPass.js'
import { UnrealBloomPass } from 'three/examples/jsm/postprocessing/UnrealBloomPass.js'
import worldData from 'world-atlas/countries-110m.json'

// ── Land mask ─────────────────────────────────────────────────────────────────
function buildLandMask(countries) {
  const W = 1024, H = 512
  const canvas = document.createElement('canvas')
  canvas.width = W; canvas.height = H
  const ctx = canvas.getContext('2d')
  ctx.fillStyle = '#000'; ctx.fillRect(0, 0, W, H)
  ctx.fillStyle = '#fff'
  for (const f of countries.features) {
    const draw = (ring) => {
      ctx.beginPath()
      ring.forEach(([lon, lat], i) => {
        const x = ((lon + 180) / 360) * W
        const y = ((90 - lat) / 180) * H
        i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y)
      })
      ctx.closePath(); ctx.fill()
    }
    const { type, coordinates } = f.geometry
    if (type === 'Polygon') draw(coordinates[0])
    else if (type === 'MultiPolygon') coordinates.forEach(p => draw(p[0]))
  }
  return { data: ctx.getImageData(0, 0, W, H).data, W, H }
}

function isLand({ data, W, H }, lon, lat) {
  const x = Math.min(W - 1, Math.floor(((lon + 180) / 360) * W))
  const y = Math.min(H - 1, Math.floor(((90 - lat)  / 180) * H))
  return data[(y * W + x) * 4] > 128
}

function lonLatToVec3(lon, lat, r = 1) {
  const phi   = (90 - lat)  * (Math.PI / 180)
  const theta = (lon + 180) * (Math.PI / 180)
  return new THREE.Vector3(
    -r * Math.sin(phi) * Math.cos(theta),
     r * Math.cos(phi),
     r * Math.sin(phi) * Math.sin(theta),
  )
}

function makeCircleTexture() {
  const size = 64
  const canvas = document.createElement('canvas')
  canvas.width = size; canvas.height = size
  const ctx = canvas.getContext('2d')
  const g = ctx.createRadialGradient(size/2, size/2, 0, size/2, size/2, size/2)
  g.addColorStop(0,   'rgba(255,255,255,1)')
  g.addColorStop(0.4, 'rgba(255,255,255,0.9)')
  g.addColorStop(1,   'rgba(255,255,255,0)')
  ctx.fillStyle = g; ctx.fillRect(0, 0, size, size)
  return new THREE.CanvasTexture(canvas)
}

// Build arc curve between two Vec3 points elevated above sphere
function makeArcPoints(a, b, R, segments = 80) {
  const pts = []
  const mid = a.clone().add(b).normalize().multiplyScalar(R + a.distanceTo(b) * 0.6)
  const curve = new THREE.QuadraticBezierCurve3(
    a.clone().normalize().multiplyScalar(R),
    mid,
    b.clone().normalize().multiplyScalar(R),
  )
  return curve.getPoints(segments)
}

// ── Component ─────────────────────────────────────────────────────────────────
export default function Globe() {
  const mountRef = useRef(null)

  useEffect(() => {
    const el = mountRef.current
    if (!el) return

    const mask = buildLandMask(feature(worldData, worldData.objects.countries))

    // Renderer
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true })
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.5))
    renderer.setSize(el.clientWidth, el.clientHeight)
    renderer.setClearColor(0x0a0a0a, 0)
    renderer.toneMapping = THREE.ACESFilmicToneMapping
    renderer.toneMappingExposure = 1
    el.appendChild(renderer.domElement)

    const scene  = new THREE.Scene()
    const camera = new THREE.PerspectiveCamera(45, el.clientWidth / el.clientHeight, 0.1, 1000)
    camera.position.z = 3.1

    const composer = new EffectComposer(renderer)
    composer.addPass(new RenderPass(scene, camera))
    const bloom = new UnrealBloomPass(
      new THREE.Vector2(el.clientWidth, el.clientHeight), 1.0, 0.4, 0.15,
    )
    composer.addPass(bloom)

    const globe = new THREE.Group()
    scene.add(globe)
    const R = 1

    // ── Land dots ──────────────────────────────────────────────
    const landVecs = []   // reuse for arc endpoints
    const positions = []
    const dotTex = makeCircleTexture()

    for (let i = 0; i < 60000; i++) {
      const lon = Math.random() * 360 - 180
      const lat = Math.random() * 180 - 90
      if (!isLand(mask, lon, lat)) continue
      const v = lonLatToVec3(lon, lat, R)
      positions.push(v.x, v.y, v.z)
      if (Math.random() < 0.015) landVecs.push(v.clone()) // sample ~900 for arcs
    }

    const dotGeo = new THREE.BufferGeometry()
    dotGeo.setAttribute('position', new THREE.BufferAttribute(new Float32Array(positions), 3))
    globe.add(new THREE.Points(dotGeo, new THREE.PointsMaterial({
      color: 0xff3333, size: 0.012, map: dotTex,
      transparent: true, opacity: 0.9, alphaTest: 0.01,
      sizeAttenuation: true, depthWrite: false,
    })))

    // ── Atmospheric rim ─────────────────────────────────────────
    globe.add(new THREE.Mesh(new THREE.SphereGeometry(R * 1.15, 48, 48), new THREE.ShaderMaterial({
      uniforms: { glowColor: { value: new THREE.Color(0xff2200) } },
      vertexShader: `varying vec3 vNormal; void main() { vNormal = normalize(normalMatrix * normal); gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }`,
      fragmentShader: `uniform vec3 glowColor; varying vec3 vNormal; void main() { float i = pow(0.65 - dot(vNormal,vec3(0,0,1)),3.0); gl_FragColor = vec4(glowColor, i*0.9); }`,
      side: THREE.FrontSide, blending: THREE.AdditiveBlending, transparent: true, depthWrite: false,
    })))

    globe.add(new THREE.Mesh(new THREE.SphereGeometry(R, 48, 48),
      new THREE.MeshBasicMaterial({ color: 0xff1a00, transparent: true, opacity: 0.04 })))

    // ── Arc system ─────────────────────────────────────────────
    const ARC_SEGMENTS  = 80
    const MAX_ARCS      = 4
    const activeArcs    = []

    const arcLineMat = () => new THREE.LineBasicMaterial({
      color: 0xffffff, transparent: true, opacity: 0.7,
      blending: THREE.AdditiveBlending, depthWrite: false,
    })

    function spawnArc() {
      if (landVecs.length < 2) return
      const a = landVecs[Math.floor(Math.random() * landVecs.length)]
      let b
      do { b = landVecs[Math.floor(Math.random() * landVecs.length)] }
      while (b === a)

      const pts     = makeArcPoints(a, b, R, ARC_SEGMENTS)
      const lineGeo = new THREE.BufferGeometry().setFromPoints(pts)
      lineGeo.setDrawRange(0, 0)
      const line = new THREE.Line(lineGeo, arcLineMat())
      globe.add(line)

      // Each arc gets its own head material so fade can mutate it directly
      const arcHeadMat = new THREE.PointsMaterial({
        color: 0xffffff, size: 0.022, map: dotTex,
        transparent: true, opacity: 1.0, alphaTest: 0.01,
        sizeAttenuation: true, depthWrite: false,
        blending: THREE.AdditiveBlending,
      })
      const headGeo = new THREE.BufferGeometry()
      headGeo.setAttribute('position', new THREE.BufferAttribute(new Float32Array(3), 3))
      const head = new THREE.Points(headGeo, arcHeadMat)
      globe.add(head)

      activeArcs.push({ line, lineGeo, head, headGeo, pts, progress: 0, phase: 'draw', hold: 0, opacity: 0.7 })
    }

    function updateArcs() {
      for (let i = activeArcs.length - 1; i >= 0; i--) {
        const arc = activeArcs[i]

        if (arc.phase === 'draw') {
          arc.progress = Math.min(1, arc.progress + 0.003)
          const drawn = Math.floor(arc.progress * ARC_SEGMENTS)
          arc.lineGeo.setDrawRange(0, drawn + 1)

          // Move head to tip
          const tip = arc.pts[drawn]
          const pa  = arc.headGeo.attributes.position
          pa.setXYZ(0, tip.x, tip.y, tip.z)
          pa.needsUpdate = true

          if (arc.progress >= 1) arc.phase = 'hold'

        } else if (arc.phase === 'hold') {
          arc.hold++
          if (arc.hold > 40) arc.phase = 'fade'

        } else if (arc.phase === 'fade') {
          arc.opacity -= 0.018
          arc.line.material.opacity = Math.max(0, arc.opacity)
          arc.head.material.opacity = Math.max(0, arc.opacity)
          if (arc.opacity <= 0) {
            globe.remove(arc.line)
            globe.remove(arc.head)
            arc.line.material.dispose()
            arc.head.material.dispose()
            arc.lineGeo.dispose()
            arc.headGeo.dispose()
            activeArcs.splice(i, 1)
          }
        }
      }

      // Randomly spawn new arcs
      if (activeArcs.length < MAX_ARCS && Math.random() < 0.04) spawnArc()
    }

    // ── Drag ───────────────────────────────────────────────────
    let dragging = false, px = 0, py = 0, vx = 0, vy = 0
    const down = (x, y) => { dragging = true; px = x; py = y; vx = 0; vy = 0 }
    const move = (x, y) => {
      if (!dragging) return
      vx = (x - px) * 0.005; vy = (y - py) * 0.005
      globe.rotation.y += vx; globe.rotation.x += vy; px = x; py = y
    }
    const up = () => { dragging = false }

    el.addEventListener('mousedown',    e => down(e.clientX, e.clientY))
    el.addEventListener('mousemove',    e => move(e.clientX, e.clientY))
    window.addEventListener('mouseup',  up)
    el.addEventListener('touchstart',   e => down(e.touches[0].clientX, e.touches[0].clientY), { passive: true })
    el.addEventListener('touchmove',    e => move(e.touches[0].clientX, e.touches[0].clientY), { passive: true })
    window.addEventListener('touchend', up)

    const onResize = () => {
      camera.aspect = el.clientWidth / el.clientHeight
      camera.updateProjectionMatrix()
      renderer.setSize(el.clientWidth, el.clientHeight)
      composer.setSize(el.clientWidth, el.clientHeight)
      bloom.setSize(el.clientWidth, el.clientHeight)
    }
    window.addEventListener('resize', onResize)

    let animId
    const tick = () => {
      animId = requestAnimationFrame(tick)
      if (!dragging) {
        vx *= 0.95; vy *= 0.95
        globe.rotation.y += vx + 0.0008
        globe.rotation.x += vy
      }
      updateArcs()
      composer.render()
    }
    tick()

    return () => {
      cancelAnimationFrame(animId)
      window.removeEventListener('mouseup',   up)
      window.removeEventListener('touchend',  up)
      window.removeEventListener('resize',    onResize)
      composer.dispose()
      renderer.dispose()
      dotTex.dispose()
      if (el.contains(renderer.domElement)) el.removeChild(renderer.domElement)
    }
  }, [])

  return <div ref={mountRef} className="absolute inset-0 pointer-events-auto" style={{ cursor: 'grab' }} />
}
