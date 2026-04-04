# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Backend — must run from repo root (module imports require it)
env $(cat .env | xargs) python3 -m uvicorn backend.api.main:app --port 8000 --reload

# Frontend
cd frontend && npm run dev    # dev server
cd frontend && npm run build  # catches TypeScript errors
```

## Non-obvious architecture

**Run order matters:** `/parlays` filters fixtures to the current matchday per league (lowest upcoming matchday per `competition_code`) before building any parlays.

**`predict_all_cached`** intentionally skips rule-based fallback for uncached fixtures — calling it would trigger slow data-store fetches while the warm-up thread holds cache locks. Only LLM-cached results are returned.

**Confidence parlay constants** not in `config.py` — hardcoded in `generator.py`: `MAX_CANDIDATES=20`, `N_PER_SIZE=3`, `MIN_UNIQUE_FIXTURES=2`, `REUSE_PENALTY=0.12`.

**Cold start (live mode):** Background thread warms fixtures/standings/season-matches (~35s). First `/predictions` warms LLM cache (~60s). `/parlays` returns `[]` until LLM cache is non-empty — intentional.

**Lock design:** `store.py` uses `acquire(blocking=False)` on fixtures lock; routes return `[]` immediately if warm thread holds it. `cache.py` uses 2s timeout then runs the function directly.

## Dead code / wiring gaps

**`api_football.py`** is not imported anywhere in the live data flow — `store.py` uses `football_data.py` exclusively. It exists as a secondary fetcher but is currently unwired.

**`ODDS_API_KEY` empty** → `get_all_odds()` returns `{}` in live mode, value bets are disabled, and parlay ranking falls back to confidence-based. Value bets only activate when this key is set.

## No tests

No test suite exists.
