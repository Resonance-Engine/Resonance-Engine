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
