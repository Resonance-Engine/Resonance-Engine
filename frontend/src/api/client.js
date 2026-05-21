/**
 * Resonance Engine API client.
 *
 * All calls go through the Vite proxy (/api -> localhost:8000/api).
 * Token is stored in localStorage and attached as Bearer header.
 */

const BASE = '/api'

function getToken() {
  return localStorage.getItem('re_token')
}

function authHeaders() {
  const token = getToken()
  return token ? { Authorization: `Bearer ${token}` } : {}
}

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...authHeaders(),
      ...options.headers,
    },
    ...options,
  })

  if (res.status === 401) {
    localStorage.removeItem('re_token')
    window.location.href = '/login'
    throw new Error('Unauthorized')
  }

  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.detail || `API error ${res.status}`)
  }

  return res.json()
}

// ── Auth ──────────────────────────────────────────────────────
export async function login(username, password) {
  const data = await request('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ username, password }),
  })
  localStorage.setItem('re_token', data.token)
  return data
}

export function logout() {
  localStorage.removeItem('re_token')
}

export function isLoggedIn() {
  return !!getToken()
}

// ── Signals ───────────────────────────────────────────────────
export async function listSignals(params = {}) {
  const qs = new URLSearchParams()
  if (params.limit) qs.set('limit', params.limit)
  if (params.offset) qs.set('offset', params.offset)
  if (params.ticker) qs.set('ticker', params.ticker)
  if (params.min_confidence) qs.set('min_confidence', params.min_confidence)
  const query = qs.toString()
  return request(`/signals${query ? `?${query}` : ''}`)
}

export async function getSignal(signalId) {
  return request(`/signals/${signalId}`)
}

// ── Events ────────────────────────────────────────────────────
export async function listEvents(params = {}) {
  const qs = new URLSearchParams()
  if (params.limit) qs.set('limit', params.limit)
  if (params.offset) qs.set('offset', params.offset)
  if (params.ticker) qs.set('ticker', params.ticker)
  if (params.event_type) qs.set('event_type', params.event_type)
  const query = qs.toString()
  return request(`/events${query ? `?${query}` : ''}`)
}

export async function getEvent(eventId) {
  return request(`/events/${eventId}`)
}

// ── Entities ──────────────────────────────────────────────────
export async function listEntities(params = {}) {
  const qs = new URLSearchParams()
  if (params.limit) qs.set('limit', params.limit)
  if (params.name_contains) qs.set('name_contains', params.name_contains)
  const query = qs.toString()
  return request(`/entities${query ? `?${query}` : ''}`)
}

export async function getEntity(ticker) {
  return request(`/entities/${ticker}`)
}

// ── Pipeline ──────────────────────────────────────────────────
export async function runPipeline(rawText, options = {}) {
  return request('/pipeline/run', {
    method: 'POST',
    body: JSON.stringify({
      raw_text: rawText,
      source: options.source || 'SEC_EDGAR',
      url: options.url || '',
      filing_type: options.filing_type || null,
      cik: options.cik || null,
    }),
  })
}

// ── Health ────────────────────────────────────────────────────
export async function checkHealth() {
  return request('/health')
}

// ── WebSocket ────────────────────────────────────────────────
/**
 * Connect to the real-time signal WebSocket.
 *
 * @param {object} handlers
 * @param {function} handlers.onSignal  - called with signal data object
 * @param {function} handlers.onCatchUp - called with array of recent signals
 * @param {function} handlers.onOpen    - called when connection opens
 * @param {function} handlers.onClose   - called when connection closes
 * @returns {{ close: function }} control handle
 */
export function connectSignalWS({ onSignal, onCatchUp, onOpen, onClose }) {
  const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const url = `${proto}//${window.location.host}/api/ws`
  let ws = null
  let pingInterval = null
  let shouldReconnect = true

  function connect() {
    ws = new WebSocket(url)

    ws.onopen = () => {
      onOpen?.()
      // Keepalive ping every 30s
      pingInterval = setInterval(() => {
        if (ws?.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ type: 'ping' }))
        }
      }, 30000)
    }

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data)
        if (msg.type === 'signal') {
          onSignal?.(msg.data)
        } else if (msg.type === 'catch_up') {
          onCatchUp?.(msg.data)
        }
      } catch { /* ignore malformed messages */ }
    }

    ws.onclose = () => {
      clearInterval(pingInterval)
      onClose?.()
      // Auto-reconnect after 3s
      if (shouldReconnect) {
        setTimeout(connect, 3000)
      }
    }

    ws.onerror = () => {
      ws?.close()
    }
  }

  connect()

  return {
    close() {
      shouldReconnect = false
      clearInterval(pingInterval)
      ws?.close()
    },
  }
}

// ── Admin helpers ────────────────────────────────────────────
export async function getAdminStats() {
  const [health, signals, events] = await Promise.all([
    checkHealth().catch(() => ({ status: 'unavailable', database: 'unavailable' })),
    listSignals({ limit: 1 }).catch(() => null),
    listEvents({ limit: 1 }).catch(() => null),
  ])
  return {
    health,
    totalSignals: signals?.total ?? 0,
    totalEvents: events?.total ?? 0,
    apiConnected: health.status !== 'unavailable',
  }
}
