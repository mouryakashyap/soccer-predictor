"""
API-Football v3 fetcher (https://v3.football.api-sports.io).

Free plan constraints:
  - No `next=` or `last=` parameters
  - 100 requests/day → caching is critical

We use this for team statistics and H2H records (season-based).
Fixture schedules are kept as mock data since upcoming fixtures
require a paid plan.
"""
import httpx
from typing import Dict, List, Optional

from backend.config import API_FOOTBALL_KEY, CURRENT_SEASON
from backend.data.cache import ttl_cache

BASE_URL  = "https://v3.football.api-sports.io"
STATS_SEASON = CURRENT_SEASON

# Hardcoded team → (team_id, league_id) for the teams in our fixture list.
# Saves API lookups (~14 requests) every startup.
TEAM_ID_MAP: Dict[str, tuple] = {
    # Premier League (39)
    "Manchester City": (50,  39),
    "Arsenal":         (42,  39),
    "Liverpool":       (40,  39),
    "Chelsea":         (49,  39),
    # La Liga (140)
    "Real Madrid":     (541, 140),
    "Barcelona":       (529, 140),
    "Atletico Madrid": (530, 140),
    "Sevilla":         (536, 140),
    # Bundesliga (78)
    "Bayern Munich":   (157, 78),
    "Borussia Dortmund": (165, 78),
    # Ligue 1 (61)
    "PSG":             (85,  61),
    "Marseille":       (81,  61),
    # Serie A (135)
    "Inter Milan":     (505, 135),
    "AC Milan":        (489, 135),
}


def _headers() -> Dict[str, str]:
    return {"x-apisports-key": API_FOOTBALL_KEY}


def _get(path: str, params: Dict) -> Dict:
    resp = httpx.get(f"{BASE_URL}{path}", headers=_headers(), params=params, timeout=10)
    resp.raise_for_status()
    return resp.json()


def resolve_team(name: str) -> Optional[tuple]:
    """
    Returns (team_id, league_id) for a team name.
    Checks hardcoded map first; falls back to API lookup (costs 1 request).
    """
    if name in TEAM_ID_MAP:
        return TEAM_ID_MAP[name]
    data = _get("/teams", {"name": name, "season": STATS_SEASON})
    items = data.get("response", [])
    if items:
        t = items[0]
        league_id = t.get("league", {}).get("id") or 39
        return (t["team"]["id"], league_id)
    return None


# ---------------------------------------------------------------------------
# Team statistics
# ---------------------------------------------------------------------------

@ttl_cache(seconds=3600)
def fetch_team_stats(team_id: int, league_id: int, season: int = STATS_SEASON) -> Dict:
    """
    Returns team stats normalised to our internal format.
    """
    data = _get("/teams/statistics", {"team": team_id, "league": league_id, "season": season})
    r = data.get("response", {})

    # Form string like "WWDLWWW..." — take last 5, most-recent last
    form_str = r.get("form", "") or ""
    last_5 = [c for c in reversed(form_str) if c in ("W", "D", "L")][:5]

    goals_for  = float((r.get("goals", {}).get("for",     {}).get("average", {}) or {}).get("total") or 1.5)
    goals_agst = float((r.get("goals", {}).get("against", {}).get("average", {}) or {}).get("total") or 1.5)

    played       = (r.get("fixtures", {}).get("played", {}) or {}).get("total") or 1
    clean_sheets = (r.get("clean_sheet", {})    or {}).get("total") or 0
    failed_score = (r.get("failed_to_score", {}) or {}).get("total") or 0

    clean_sheet_rate = round(max(0.0, min(1.0, clean_sheets / played)), 3)
    btts_rate        = round(max(0.1, min(0.9, 1 - clean_sheet_rate - (failed_score / played))), 3)

    return {
        "last_5":             last_5 or ["D", "D", "D", "D", "D"],
        "goals_scored_avg":   goals_for,
        "goals_conceded_avg": goals_agst,
        "btts_rate":          btts_rate,
        "clean_sheet_rate":   clean_sheet_rate,
        "league_position":    10,  # standings endpoint is separate; small impact on model
    }


# ---------------------------------------------------------------------------
# Head-to-head
# ---------------------------------------------------------------------------

@ttl_cache(seconds=3600)
def fetch_h2h(home_team_id: int, away_team_id: int, seasons: tuple = (2024, 2023)) -> List[str]:
    """
    Returns up to 5 H2H results as W/D/L from home_team_id's perspective.
    Queries multiple seasons (free plan doesn't support `last=N`).
    """
    results: List[str] = []
    for season in seasons:
        if len(results) >= 5:
            break
        data = _get(
            "/fixtures/headtohead",
            {"h2h": f"{home_team_id}-{away_team_id}", "season": season},
        )
        for match in data.get("response", []):
            teams = match["teams"]
            # Determine result from home_team_id's perspective
            if teams["home"]["id"] == home_team_id:
                winner_flag = teams["home"]["winner"]
            else:
                winner_flag = teams["away"]["winner"]

            if winner_flag is True:
                results.append("W")
            elif winner_flag is None:
                results.append("D")
            else:
                results.append("L")

    return results[:5]
