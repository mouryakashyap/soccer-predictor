"""
Data access layer.

USE_MOCK_DATA=true  (default) → everything from hard-coded mock data.
USE_MOCK_DATA=false           → hybrid mode:
    - Fixtures   : football-data.org (current season, real upcoming matches)
    - Team stats : football-data.org (standings + recent match history)
    - H2H        : football-data.org (scanned from team match history)
    - Odds       : mock until The Odds API key is configured

The public interface is identical in both modes.
"""
from backend.config import USE_MOCK_DATA
from backend.data.mock_data import FIXTURES, ODDS, TEAM_STATS, H2H as _H2H_DATA


# ---------------------------------------------------------------------------
# Mock mode
# ---------------------------------------------------------------------------
if USE_MOCK_DATA:

    def get_fixtures():
        return FIXTURES

    def get_odds(fixture_id: str):
        return ODDS.get(fixture_id)

    def get_team_stats(team: str):
        return TEAM_STATS.get(team)

    def get_h2h(home_team: str, away_team: str):
        return _H2H_DATA.get((home_team, away_team), [])

    def get_all_odds():
        return ODDS

# ---------------------------------------------------------------------------
# Live mode (football-data.org fixtures/stats + mock odds)
# ---------------------------------------------------------------------------
else:
    from typing import Dict, List, Optional

    from backend.data.fetchers.football_data import (
        fetch_upcoming_fixtures,
        fetch_team_stats as _fetch_team_stats,
        fetch_h2h as _fetch_h2h,
    )

    # team_name → (team_id, competition_code) — populated on first get_fixtures() call
    import threading as _threading
    _team_meta: Dict[str, tuple] = {}
    _fixtures_cache: Optional[List[Dict]] = None
    _fixtures_lock = _threading.Lock()

    def _load_fixtures() -> List[Dict]:
        global _fixtures_cache
        if _fixtures_cache is not None:
            return _fixtures_cache
        # Non-blocking try: if another thread is already fetching, return
        # empty immediately so routes stay responsive during warm-up.
        acquired = _fixtures_lock.acquire(blocking=False)
        if not acquired:
            return []
        try:
            # Re-check inside lock
            if _fixtures_cache is not None:
                return _fixtures_cache
            fixtures = fetch_upcoming_fixtures()
            for f in fixtures:
                _team_meta[f["home_team"]] = (f["home_team_id"], f["competition_code"])
                _team_meta[f["away_team"]] = (f["away_team_id"], f["competition_code"])
            _fixtures_cache = fixtures
            return fixtures
        finally:
            _fixtures_lock.release()

    def get_fixtures() -> List[Dict]:
        return _load_fixtures()

    def get_odds(fixture_id: str) -> Optional[Dict]:
        # Odds API not yet connected — return None so predictions still show without value bets
        return None

    def get_team_stats(team: str) -> Optional[Dict]:
        if team not in _team_meta:
            _load_fixtures()
        if team not in _team_meta:
            return TEAM_STATS.get(team)   # fall back to mock for unknown teams
        team_id, competition_code = _team_meta[team]
        try:
            return _fetch_team_stats(team_id, competition_code)
        except Exception:
            return TEAM_STATS.get(team)

    def get_h2h(home_team: str, away_team: str) -> List[str]:
        if home_team not in _team_meta or away_team not in _team_meta:
            _load_fixtures()
        if home_team not in _team_meta or away_team not in _team_meta:
            return _H2H_DATA.get((home_team, away_team), [])
        home_id, competition_code = _team_meta[home_team]
        away_id, _                = _team_meta[away_team]
        try:
            return _fetch_h2h(home_id, away_id, competition_code)
        except Exception:
            return _H2H_DATA.get((home_team, away_team), [])

    def get_all_odds() -> Dict:
        return {}
