# Claude Checkpoint

## Session Summary
Date: 2026-04-03

## Decisions Made

- **Parlay size defaults**: `MIN_PARLAY_SIZE=4`, `MAX_PARLAY_SIZE=7` — set as code defaults in `config.py` (not just `.env` overrides). CLAUDE.md updated to match.
- **Season config**: `api_football.py` was hardcoding `STATS_SEASON = 2024`. Changed to use `CURRENT_SEASON` from `config.py` (auto-detects: Aug+ = current year, Jan–Jul = prev year). Stale docstring note about "2022–2024 only" removed.
- **CLAUDE.md improvements**: Added missing config vars (`API_FOOTBALL_KEY`, `CURRENT_SEASON`), added "No test suite" note, fixed previously wrong parlay size defaults.

## Files Touched

| File | Change |
|------|--------|
| `backend/config.py` | Changed `MIN_PARLAY_SIZE` default `2→4`, `MAX_PARLAY_SIZE` default `5→7` |
| `backend/data/fetchers/api_football.py` | Replaced hardcoded `STATS_SEASON = 2024` with `STATS_SEASON = CURRENT_SEASON`; removed outdated free-plan season constraint note |
| `CLAUDE.md` | Fixed parlay size defaults; added `API_FOOTBALL_KEY` and `CURRENT_SEASON` to config table; added Tests section |

## Current State

- Both servers running:
  - Backend: `http://localhost:8000` (FastAPI, `USE_MOCK_DATA=false`, `USE_LLM_PREDICTOR=true`)
  - Frontend: `http://localhost:5173` (Vite + React)
- Live mode active — fetches real fixtures from football-data.org
- LLM predictions via OpenAI GPT-4o (first `/predictions` call ~60s cold, instant after cache warms)

## Blockers / Open Items

- `api_football.py` is not imported anywhere in the live data flow (`store.py` uses `football_data.py` exclusively). It exists as a secondary fetcher but is currently unused — if it's meant to be wired in, that work hasn't been done.
- No test suite exists. No pytest config, no test files.
- `ODDS_API_KEY` is empty in `.env` — value bets and EV parlays are disabled; parlay ranking falls back to confidence-based.
