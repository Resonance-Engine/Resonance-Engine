// ── Mock data for admin pages ─────────────────────────────────
// Replace with real Supabase queries once wired up

export const adminStats = {
  totalUsers: 1247,
  activeSignals: 89,
  eventsToday: 342,
  pipelineHealth: 97.3,
  signalsGenerated24h: 156,
  avgConfidence: 0.74,
}

export const recentActivity = [
  { id: 1, type: 'signal',   message: 'New high-confidence signal: AAPL earnings beat',    time: '2m ago' },
  { id: 2, type: 'user',     message: 'New user registered: sarah.chen@trading.io',        time: '8m ago' },
  { id: 3, type: 'pipeline', message: 'EDGAR ingestion cycle completed (23 filings)',      time: '14m ago' },
  { id: 4, type: 'signal',   message: 'Signal confidence updated: TSLA FDA catalyst',      time: '21m ago' },
  { id: 5, type: 'error',    message: 'NewsAPI rate limit hit — retry scheduled in 42s',   time: '28m ago' },
  { id: 6, type: 'user',     message: 'User role changed: admin@resonance.io → admin',     time: '35m ago' },
  { id: 7, type: 'pipeline', message: 'GDELT scan completed (87 events extracted)',        time: '41m ago' },
  { id: 8, type: 'signal',   message: 'Signal expired: NVDA supply chain disruption',      time: '52m ago' },
]

export const mockUsers = [
  { id: 'usr_001', name: 'Reiyyan Z.',      email: 'reiyyan@resonance.io',      role: 'admin',  status: 'active',    lastActive: '2 min ago',   signalsViewed: 421 },
  { id: 'usr_002', name: 'Sarah Chen',      email: 'sarah.chen@trading.io',     role: 'user',   status: 'active',    lastActive: '8 min ago',   signalsViewed: 87 },
  { id: 'usr_003', name: 'Marcus Webb',     email: 'mwebb@quant.fund',          role: 'user',   status: 'active',    lastActive: '1 hr ago',    signalsViewed: 234 },
  { id: 'usr_004', name: 'Lina Torres',     email: 'ltorres@hedgeco.com',       role: 'user',   status: 'active',    lastActive: '3 hrs ago',   signalsViewed: 156 },
  { id: 'usr_005', name: 'James Okafor',    email: 'jokafor@fintech.dev',       role: 'user',   status: 'suspended', lastActive: '2 days ago',  signalsViewed: 12 },
  { id: 'usr_006', name: 'Ava Petrov',      email: 'apetrov@alpha.capital',     role: 'user',   status: 'active',    lastActive: '15 min ago',  signalsViewed: 309 },
  { id: 'usr_007', name: 'Dev Account',     email: 'dev@resonance.io',          role: 'admin',  status: 'active',    lastActive: '5 min ago',   signalsViewed: 1043 },
  { id: 'usr_008', name: 'Kai Nakamura',    email: 'kai.n@deepvalue.ai',        role: 'user',   status: 'inactive',  lastActive: '14 days ago', signalsViewed: 3 },
]

export const mockSignals = [
  { id: 'sig_001', ticker: 'AAPL',  type: 'earnings_beat',     confidence: 0.92, status: 'active',  timestamp: '2026-03-30T14:23:00Z', impact: '24h', summary: 'Q1 earnings beat by 14% — record services revenue cited' },
  { id: 'sig_002', ticker: 'TSLA',  type: 'fda_catalyst',      confidence: 0.78, status: 'active',  timestamp: '2026-03-30T13:11:00Z', impact: '1w',  summary: 'Robotaxi regulatory filing submitted to NHTSA' },
  { id: 'sig_003', ticker: 'NVDA',  type: 'supply_disruption', confidence: 0.65, status: 'expired', timestamp: '2026-03-30T09:45:00Z', impact: '4h',  summary: 'Taiwan fab capacity reallocation — H100 line affected' },
  { id: 'sig_004', ticker: 'MSFT',  type: 'partnership',       confidence: 0.88, status: 'active',  timestamp: '2026-03-30T12:00:00Z', impact: '24h', summary: 'Azure-OpenAI enterprise deal with Saudi Aramco announced' },
  { id: 'sig_005', ticker: 'JPM',   type: 'legal_risk',        confidence: 0.71, status: 'active',  timestamp: '2026-03-30T11:30:00Z', impact: '1w',  summary: 'DOJ antitrust probe expanded to retail banking division' },
  { id: 'sig_006', ticker: 'META',  type: 'earnings_miss',     confidence: 0.84, status: 'active',  timestamp: '2026-03-30T10:15:00Z', impact: '24h', summary: 'Reality Labs losses exceed guidance by $800M' },
  { id: 'sig_007', ticker: 'AMZN',  type: 'acquisition',       confidence: 0.69, status: 'pending', timestamp: '2026-03-30T08:50:00Z', impact: '1w',  summary: 'Rumored acquisition of autonomous logistics startup' },
  { id: 'sig_008', ticker: 'GOOG',  type: 'regulatory',        confidence: 0.76, status: 'active',  timestamp: '2026-03-29T22:10:00Z', impact: '1w',  summary: 'EU Digital Markets Act compliance deadline — search remedies' },
]

export const mockEvents = [
  { id: 'evt_001', source: 'EDGAR',   type: '8-K',        entities: ['AAPL'],        timestamp: '2026-03-30T14:20:00Z', status: 'processed', summary: 'Apple Inc. — Results of Operations and Financial Condition' },
  { id: 'evt_002', source: 'EDGAR',   type: '8-K',        entities: ['META'],        timestamp: '2026-03-30T10:12:00Z', status: 'processed', summary: 'Meta Platforms — Quarterly earnings press release' },
  { id: 'evt_003', source: 'NewsAPI', type: 'headline',   entities: ['TSLA'],        timestamp: '2026-03-30T13:08:00Z', status: 'processed', summary: 'Tesla submits robotaxi safety framework to NHTSA' },
  { id: 'evt_004', source: 'GDELT',   type: 'geopolitical', entities: ['NVDA','TSM'], timestamp: '2026-03-30T09:40:00Z', status: 'processed', summary: 'Taiwan semiconductor policy shift impacts export allocations' },
  { id: 'evt_005', source: 'NewsAPI', type: 'headline',   entities: ['MSFT'],        timestamp: '2026-03-30T11:55:00Z', status: 'processed', summary: 'Microsoft and Saudi Aramco sign $2B cloud infrastructure deal' },
  { id: 'evt_006', source: 'EDGAR',   type: '10-K',       entities: ['JPM'],         timestamp: '2026-03-30T11:25:00Z', status: 'processed', summary: 'JPMorgan Chase — Annual report with risk factor updates' },
  { id: 'evt_007', source: 'NewsAPI', type: 'headline',   entities: ['AMZN'],        timestamp: '2026-03-30T08:45:00Z', status: 'pending',   summary: 'Sources: Amazon in talks to acquire autonomous delivery firm' },
  { id: 'evt_008', source: 'GDELT',   type: 'regulatory', entities: ['GOOG'],        timestamp: '2026-03-29T22:05:00Z', status: 'processed', summary: 'EU antitrust body issues compliance deadline for Google Search' },
  { id: 'evt_009', source: 'EDGAR',   type: '8-K',        entities: ['COIN'],        timestamp: '2026-03-29T20:30:00Z', status: 'error',     summary: 'Coinbase — Material cybersecurity incident disclosure' },
  { id: 'evt_010', source: 'NewsAPI', type: 'headline',   entities: ['SPY','QQQ'],   timestamp: '2026-03-29T18:00:00Z', status: 'processed', summary: 'Fed signals pause — markets rally on dovish pivot' },
]

export const mockPipeline = {
  sources: [
    { name: 'EDGAR',   status: 'running', lastRun: '14 min ago', eventsToday: 23,  errors: 0, nextRun: '1 min' },
    { name: 'NewsAPI', status: 'idle',    lastRun: '28 min ago', eventsToday: 187, errors: 1, nextRun: '2 min' },
    { name: 'GDELT',   status: 'idle',    lastRun: '41 min ago', eventsToday: 132, errors: 0, nextRun: '19 min' },
  ],
  recentTasks: [
    { id: 'tsk_001', source: 'EDGAR',   status: 'completed', duration: '4.2s',  events: 23,  started: '14 min ago' },
    { id: 'tsk_002', source: 'GDELT',   status: 'completed', duration: '8.1s',  events: 87,  started: '41 min ago' },
    { id: 'tsk_003', source: 'NewsAPI', status: 'completed', duration: '2.8s',  events: 45,  started: '28 min ago' },
    { id: 'tsk_004', source: 'EDGAR',   status: 'completed', duration: '3.9s',  events: 18,  started: '1 hr ago' },
    { id: 'tsk_005', source: 'NewsAPI', status: 'failed',    duration: '12.4s', events: 0,   started: '1 hr ago', error: 'Rate limit exceeded (429)' },
    { id: 'tsk_006', source: 'GDELT',   status: 'completed', duration: '6.7s',  events: 45,  started: '2 hrs ago' },
  ],
}
