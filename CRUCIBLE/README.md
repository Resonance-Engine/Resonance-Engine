# CRUCIBLE — Resonance Engine Research Function

Where research bets get tested until they break or prove out. This folder is the
persistent home of the founding-research-lead function: every bet, experiment,
and finding lives here so future sessions (and humans) can pick up exactly where
the last one stopped.

## Structure

```
CRUCIBLE/
├── README.md          ← you are here
├── CHARTER.md         ← the master prompt / operating rules for the research lead
├── BETS.md            ← the active bets register (max 3 active, each falsifiable)
├── findings/          ← numbered findings — question, method, data, result, DECISION
├── experiments/       ← reproducible scripts, one per experiment (exp###_*.py)
└── data/              ← small cached datasets experiments depend on (never secrets)
```

## Rules of the house

- Every finding ends with a **decision**, not a vibe. "Kill", "scale", or "blocked on X".
- Every experiment is a rerunnable script under `experiments/` — no notebook archaeology.
- No experiment may spend paid API credits without an explicit cost ceiling written
  in the script header. Free sources (EDGAR history, Stooq daily bars) preferred.
- Negative results are first-class citizens. A cleanly killed bet is shipped work.
- Postgres is production. Never `docker compose down -v`.

## Reading order for a new session

1. `BETS.md` — what's active, what's killed, what's blocked
2. `findings/` in reverse numeric order — most recent conclusions first
3. `CHARTER.md` — if you need to re-anchor on the mission
