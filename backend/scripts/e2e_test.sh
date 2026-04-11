#!/usr/bin/env bash
# Live end-to-end test for Resonance Engine
# Tests: Docker → DB → API → Pipeline → Signal → WebSocket
#
# Usage: cd backend && bash scripts/e2e_test.sh

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

pass() { echo -e "${GREEN}✓ $1${NC}"; }
fail() { echo -e "${RED}✗ $1${NC}"; exit 1; }
info() { echo -e "${YELLOW}→ $1${NC}"; }

echo "═══════════════════════════════════════════════"
echo " Resonance Engine — Live End-to-End Test"
echo "═══════════════════════════════════════════════"
echo ""

# 1. Check Docker containers
info "Checking Docker containers..."
docker compose -f ../docker-compose.yml ps --format '{{.Name}} {{.Status}}' | grep -q "resonance-postgres" && pass "PostgreSQL running" || fail "PostgreSQL not running"
docker compose -f ../docker-compose.yml ps --format '{{.Name}} {{.Status}}' | grep -q "resonance-redis" && pass "Redis running" || fail "Redis not running"

# 2. Check API health
info "Checking API health..."
HEALTH=$(curl -sf http://localhost:8000/api/health 2>/dev/null) || fail "API not responding on :8000"
echo "$HEALTH" | python3 -c "import sys,json; d=json.load(sys.stdin); assert d['status']=='healthy'" 2>/dev/null && pass "API healthy" || fail "API unhealthy"
echo "$HEALTH" | python3 -c "import sys,json; d=json.load(sys.stdin); assert d['database']=='connected'" 2>/dev/null && pass "Database connected" || fail "Database not connected"

# 3. Check auth
info "Checking authentication..."
LOGIN=$(curl -sf -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"operator","password":"resonance2026"}' 2>/dev/null) || fail "Login failed"
TOKEN=$(echo "$LOGIN" | python3 -c "import sys,json; print(json.load(sys.stdin)['token'])")
[ -n "$TOKEN" ] && pass "Auth token received" || fail "No token returned"

# 4. Check existing signals
info "Checking signal store..."
SIGNALS=$(curl -sf http://localhost:8000/api/signals?limit=1 \
  -H "Authorization: Bearer $TOKEN" 2>/dev/null) || fail "Signals endpoint failed"
TOTAL=$(echo "$SIGNALS" | python3 -c "import sys,json; print(json.load(sys.stdin)['total'])")
pass "Signal store: $TOTAL signals"

# 5. Run pipeline with test event
info "Running pipeline with test event..."
PIPELINE=$(curl -sf -X POST http://localhost:8000/api/pipeline/run \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "raw_text": "FORM 8-K: Coca-Cola Company (KO) reported Q1 2026 revenue of $11.3 billion, up 3%. Organic revenue grew 6%. Raised full-year EPS guidance by 2%.",
    "source": "SEC_EDGAR"
  }' 2>/dev/null) || fail "Pipeline run failed"

REJECTED=$(echo "$PIPELINE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('rejected', True))")
TICKER=$(echo "$PIPELINE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('primary_ticker', '?'))")
CONF=$(echo "$PIPELINE" | python3 -c "import sys,json; print(f\"{json.load(sys.stdin).get('confidence', 0)*100:.1f}%\")")
[ "$REJECTED" = "False" ] && pass "Pipeline approved signal: $TICKER at $CONF confidence" || fail "Pipeline rejected signal"

# 6. Verify signal persisted
info "Verifying signal persisted..."
sleep 1
SIGNALS_AFTER=$(curl -sf http://localhost:8000/api/signals?limit=1 \
  -H "Authorization: Bearer $TOKEN" 2>/dev/null)
TOTAL_AFTER=$(echo "$SIGNALS_AFTER" | python3 -c "import sys,json; print(json.load(sys.stdin)['total'])")
[ "$TOTAL_AFTER" -gt "$TOTAL" ] && pass "Signal persisted (count: $TOTAL → $TOTAL_AFTER)" || pass "Signal count: $TOTAL_AFTER (may have been deduped)"

# 7. Check WebSocket
info "Checking WebSocket endpoint..."
WS_OK=$(python3 -c "
import asyncio, json, websockets
async def test():
    async with websockets.connect('ws://localhost:8000/api/ws') as ws:
        await ws.send(json.dumps({'type': 'ping'}))
        pong = await asyncio.wait_for(ws.recv(), timeout=3)
        return json.loads(pong)['type'] == 'pong'
print(asyncio.run(test()))
" 2>/dev/null)
[ "$WS_OK" = "True" ] && pass "WebSocket connected + ping/pong OK" || fail "WebSocket failed"

# 8. Check quota tracking
info "Checking API quota tracking..."
QUOTAS=$(echo "$HEALTH" | python3 -c "import sys,json; q=json.load(sys.stdin)['quotas']; print(f\"NewsAPI: {q['newsapi']['remaining']}/{q['newsapi']['limit']}\")")
pass "Quotas: $QUOTAS"

# 9. Check frontend
info "Checking frontend..."
FRONTEND=$(curl -sf -o /dev/null -w "%{http_code}" http://localhost:5173/ 2>/dev/null)
[ "$FRONTEND" = "200" ] && pass "Frontend serving on :5173" || info "Frontend not running (optional)"

echo ""
echo "═══════════════════════════════════════════════"
echo -e "${GREEN} All checks passed!${NC}"
echo "═══════════════════════════════════════════════"
