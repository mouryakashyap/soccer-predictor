# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Backend (Python / FastAPI)
```bash
# Run server (from repo root — must be run from root for module imports to work)
env $(cat .env | xargs) python3 -m uvicorn backend.api.main:app --port 8000

# With auto-reload during development
env $(cat .env | xargs) python3 -m uvicorn backend.api.main:app --port 8000 --reload

# Install dependencies
pip install -r requirements.txt
```

### Frontend (React / Vite)
```bash
cd frontend
npm install
npm run dev       # dev server (auto-picks port from 5173 upward if occupied)
npm run build     # tsc + vite build (run this to catch TypeScript errors)
npm run preview   # preview production build
```

### Docker
```bash
docker-compose up --build
```

## Architecture

### Data flow (live mode)
```
football-data.org API
        ↓
backend/data/fetchers/football_data.py  (TTL-cached, rate-limited)
        ↓
backend/data/store.py  (accessor layer; mock_data.py when USE_MOCK_DATA=true)
        ↓
backend/models/features.py  (numeric feature dict from team stats + H2H)
        ↓
backend/models/predictor.py  (dispatcher: LLM first, rule-based fallback)
        ├── backend/models/llm_predictor.py  (OpenAI GPT-4o, function-calling, TTL cache)
        └── rule-based inline  (Poisson CDF for O/U, heuristics for 1X2/BTTS)
        ↓
backend/models/value.py  (edge = model_prob − implied_prob vs bookmaker odds)
        ↓
backend/parlays/generator.py  (EV-based if odds exist; confidence-based fallback)
        ↓
API routes → frontend
```

### Key architectural decisions

**Predictor dispatcher (`predictor.py`)** — three public functions with different blocking characteristics:
- `predict(fixture)` — LLM first, per-fixture rule-based fallback. Blocks during LLM call.
- `predict_all(fixtures)` — batched LLM (up to `LLM_BATCH_SIZE=10` per API call), per-fixture fallback. Used by `/predictions` route. ~60s on cold cache.
- `predict_all_cached(fixtures)` — returns **only** what's already in the LLM TTL cache; skips uncached fixtures entirely (no API calls). Used by `/parlays` route to stay non-blocking.

**Parlay generator** — two paths:
- EV path: only active when bookmaker odds exist (`ODDS_API_KEY` set). Ranks by expected value.
- Confidence fallback: active when no odds. One pick per fixture (best outcome ≥ `CONFIDENCE_THRESHOLD=0.55`), capped to top 20 candidates before combinatorics (prevents C(35,7)=6.7M explosion), returns top 3 per leg-count. Current config: `MIN_PARLAY_SIZE=4`, `MAX_PARLAY_SIZE=7`.

**Threading/caching** — in-memory only, process-scoped:
- `backend/data/cache.py`: thread-safe TTL cache with per-key `threading.Lock`, double-checked locking, 2-second `blocking=True, timeout=2` acquire (runs function directly if timeout expires rather than blocking forever).
- `backend/data/store.py` (live mode): `_fixtures_lock.acquire(blocking=False)` — if background warm thread holds the lock, routes return `[]` immediately rather than waiting 35s.
- `backend/models/llm_predictor.py`: separate module-level `_cache` dict with `LLM_CACHE_TTL_SECONDS=3600`.
- FastAPI lifespan starts a daemon thread that pre-fetches fixtures/standings/season-matches for all 5 leagues (~35s). LLM predictions are warmed on the first `/predictions` request (~60s one-time).
- `/parlays` checks `_is_prediction_cache_warm()` (non-empty LLM cache) and returns `[]` immediately if cold.

**football-data.org fetcher** — `fetch_season_matches(code)` does triple duty from one cached response: H2H filtering, last-5 form, and BTTS/clean-sheet rates. Zero additional API calls per team beyond the 3 league-level fetches (fixtures + standings + season matches). Note: the fetcher rate-limits at 7s between leagues and auto-retries 429s with a 65s sleep — this can silently stall the startup warm thread.

### API routes
| Endpoint | Description |
|----------|-------------|
| `GET /fixtures` | All upcoming fixtures |
| `GET /fixtures/:id` | Single fixture |
| `GET /predictions` | All fixtures with LLM/model probabilities + value bets |
| `GET /predictions/:id` | Single fixture prediction |
| `GET /parlays?size=&min_ev=` | Confidence-based parlays (4–7 leg), optional size filter |
| `GET /health` | Liveness check |

### Frontend structure
- `src/api/client.ts` — all API calls + TypeScript types; single source of truth for shapes. Backend URL defaults to `http://localhost:8000`; override with `VITE_API_URL` env var.
- `src/pages/Dashboard.tsx` — fetches `/predictions`, groups by **date first then league** (PL→PD→BL1→SA→FL1 within each date), sorted by kickoff time.
- `src/pages/Parlays.tsx` — fetches `/parlays`, leg-count filter buttons (All / 4 / 5 / 6 / 7 leg), hides odds/EV columns when `decimal_odds === 0`.
- `src/components/FixtureCard.tsx` — 1X2/O/U/BTTS probability grids + value bet rows.
- `src/components/ValueBadge.tsx` — edge badge: green ≥10%, yellow ≥5%, gray otherwise.
- `App.tsx` — SPA with client-side `useState` page switching (no React Router). Nav toggles between `dashboard` and `parlays` views.

## Configuration

All parameters live in `backend/config.py`, overridable via environment variables (loaded from `.env`):

| Var | Default | Effect |
|-----|---------|--------|
| `USE_MOCK_DATA` | `true` | Use hard-coded mock data instead of live APIs |
| `USE_LLM_PREDICTOR` | `false` | Enable OpenAI GPT-4o predictions |
| `OPENAI_API_KEY` | — | Required when `USE_LLM_PREDICTOR=true` |
| `LLM_MODEL` | `gpt-4o` | OpenAI model name |
| `LLM_BATCH_SIZE` | `10` | Fixtures per OpenAI API call |
| `LLM_CACHE_TTL_SECONDS` | `3600` | LLM prediction cache TTL |
| `FOOTBALL_DATA_KEY` | — | football-data.org API token (live mode) |
| `ODDS_API_KEY` | — | The Odds API key (value bets + EV parlays) |
| `API_FOOTBALL_KEY` | — | api-sports.io token (legacy fetcher, currently unused) |
| `CURRENT_SEASON` | auto-detected | Season year (auto: Aug+ = current year, Jan–Jul = prev year) |
| `VALUE_THRESHOLD` | `0.05` | Minimum edge to flag a value bet |
| `CONFIDENCE_THRESHOLD` | `0.55` | Minimum model_prob to include a pick in confidence parlays |
| `MIN_PARLAY_SIZE` | `4` | Minimum legs in a parlay |
| `MAX_PARLAY_SIZE` | `7` | Maximum legs in a parlay |
| `MIN_PARLAY_PROB` | `0.10` | Drop parlays below this combined probability |
| `TOP_N_PARLAYS` | `10` | How many parlays to return (3 per leg-count within this budget) |

## Live mode cold-start behaviour

On first request after server restart with `USE_MOCK_DATA=false`:
1. Background thread fetches fixtures + standings + season matches for 5 leagues (~35s, rate-limited at 7s/league).
2. First `/predictions` request triggers LLM batch call (~60s for 38 fixtures).
3. After step 2, all subsequent `/predictions` and `/parlays` requests are instant (cache hits).
4. `/parlays` returns `[]` until step 2 completes — this is intentional to avoid blocking.

## Tests

There is no test suite. No pytest config, no test files exist in the repo.

## Data modes

| Function | `USE_MOCK_DATA=true` | `USE_MOCK_DATA=false` |
|---|---|---|
| `get_fixtures()` | `mock_data.FIXTURES` | football-data.org (5 leagues, 7-day lookahead) |
| `get_team_stats()` | `mock_data.TEAM_STATS` | standings + season matches (cached) |
| `get_h2h()` | `mock_data.H2H` | season matches filtered by team pair |
| `get_odds()` | `mock_data.ODDS` | `None` (no ODDS_API_KEY configured) |
