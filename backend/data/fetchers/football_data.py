"""
football-data.org v4 fetcher (https://api.football-data.org/v4).

Free tier: top 5 leagues, current season, 10 requests/minute.

Cold-start cost: 15 requests total (3 batched calls per league).
All results cached 1 hour so subsequent requests are instant.

  Per league (×5):
    1. /competitions/{code}/matches?status=SCHEDULED  → upcoming fixtures
    2. /competitions/{code}/standings                 → goals avg + league position for ALL teams
    3. /competitions/{code}/matches?status=FINISHED   → season results for H2H of ANY pair
"""
import time
from datetime import date, timedelta
from typing import Dict, List, Optional, Tuple

import httpx

from backend.config import FOOTBALL_DATA_KEY
from backend.data.cache import ttl_cache

BASE_URL = "https://api.football-data.org/v4"

COMPETITION_CODES: Dict[str, str] = {
    "PL":  "Premier League",
    "PD":  "La Liga",
    "BL1": "Bundesliga",
    "FL1": "Ligue 1",
    "SA":  "Serie A",
}

# seconds to pause between league requests to stay within 10 req/min
_RATE_PAUSE = 7


def _headers() -> Dict[str, str]:
    return {"X-Auth-Token": FOOTBALL_DATA_KEY}


def _get(path: str, params: Dict = None) -> Dict:
    resp = httpx.get(f"{BASE_URL}{path}", headers=_headers(), params=params or {}, timeout=15)
    if resp.status_code == 429:
        time.sleep(65)   # wait for the 1-minute window to fully reset
        resp = httpx.get(f"{BASE_URL}{path}", headers=_headers(), params=params or {}, timeout=15)
    resp.raise_for_status()
    return resp.json()


# ---------------------------------------------------------------------------
# 1. Upcoming fixtures
# ---------------------------------------------------------------------------

@ttl_cache(seconds=3600)
def fetch_upcoming_fixtures(days_ahead: int = 7) -> List[Dict]:
    """5 requests total — one per league."""
    today   = date.today()
    date_to = today + timedelta(days=days_ahead)
    fixtures = []

    for i, (code, league_name) in enumerate(COMPETITION_CODES.items()):
        if i > 0:
            time.sleep(_RATE_PAUSE)
        data = _get(
            f"/competitions/{code}/matches",
            {"status": "SCHEDULED", "dateFrom": str(today), "dateTo": str(date_to)},
        )
        for m in data.get("matches", []):
            fixtures.append({
                "fixture_id":       str(m["id"]),
                "home_team":        m["homeTeam"]["name"],
                "away_team":        m["awayTeam"]["name"],
                "home_team_id":     m["homeTeam"]["id"],
                "away_team_id":     m["awayTeam"]["id"],
                "kickoff":          m["utcDate"],
                "league":           league_name,
                "competition_code": code,
                "season":           2025,
            })
    return fixtures


# ---------------------------------------------------------------------------
# 2. Standings — goals avg + position for every team in a league (1 request)
# ---------------------------------------------------------------------------

@ttl_cache(seconds=3600)
def fetch_competition_standings(code: str) -> Dict[int, Dict]:
    """
    Returns {team_id: {goals_scored_avg, goals_conceded_avg, league_position}}.
    One request covers ALL teams in the competition.
    """
    data  = _get(f"/competitions/{code}/standings")
    table = (data.get("standings") or [{}])[0].get("table", [])
    result: Dict[int, Dict] = {}
    for row in table:
        played = row.get("playedGames") or 1
        result[row["team"]["id"]] = {
            "goals_scored_avg":   round(row["goalsFor"]     / played, 2),
            "goals_conceded_avg": round(row["goalsAgainst"] / played, 2),
            "league_position":    row["position"],
        }
    return result


# ---------------------------------------------------------------------------
# 3. Finished season matches — used for H2H of any pair (1 request per league)
# ---------------------------------------------------------------------------

@ttl_cache(seconds=3600)
def fetch_season_matches(code: str) -> List[Dict]:
    """All finished matches for the current season in one competition."""
    data = _get(f"/competitions/{code}/matches", {"status": "FINISHED"})
    return data.get("matches", [])


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------

def _goals_for_team(match: Dict, team_id: int) -> Tuple[Optional[int], Optional[int]]:
    ft = match.get("score", {}).get("fullTime", {})
    h, a = ft.get("home"), ft.get("away")
    if h is None or a is None:
        return None, None
    return (h, a) if match["homeTeam"]["id"] == team_id else (a, h)


def fetch_team_stats(team_id: int, competition_code: str) -> Dict:
    """
    Combines standings (goals avg + position) with season match history (form, BTTS,
    clean sheet). Both data sources are already cached from startup — no extra API calls.
    """
    standing = fetch_competition_standings(competition_code).get(team_id, {})

    # Season matches are fetched in bulk; filter for this team at no API cost
    all_matches = fetch_season_matches(competition_code)
    team_matches = [
        m for m in all_matches
        if m["homeTeam"]["id"] == team_id or m["awayTeam"]["id"] == team_id
    ]

    last_5: List[str] = []
    btts = clean_sheets = total = 0

    for m in team_matches:
        scored, conceded = _goals_for_team(m, team_id)
        if scored is None:
            continue
        total += 1
        if len(last_5) < 5:
            if scored > conceded:
                last_5.append("W")
            elif scored == conceded:
                last_5.append("D")
            else:
                last_5.append("L")
        if total <= 10:
            if scored > 0 and conceded > 0:
                btts += 1
            if conceded == 0:
                clean_sheets += 1

    sample = min(total, 10) or 1

    return {
        "last_5":             last_5 or ["D", "D", "D", "D", "D"],
        "goals_scored_avg":   standing.get("goals_scored_avg",   1.5),
        "goals_conceded_avg": standing.get("goals_conceded_avg", 1.5),
        "btts_rate":          round(max(0.1, min(0.9, btts        / sample)), 3),
        "clean_sheet_rate":   round(max(0.0, min(1.0, clean_sheets / sample)), 3),
        "league_position":    standing.get("league_position", 10),
    }


def fetch_h2h(home_id: int, away_id: int, competition_code: str) -> List[str]:
    """
    Filters the cached season matches for head-to-head results.
    No extra API call — reuses the batch already fetched for this competition.
    """
    matches = fetch_season_matches(competition_code)
    results: List[str] = []
    for m in matches:
        ids = {m["homeTeam"]["id"], m["awayTeam"]["id"]}
        if {home_id, away_id} != ids:
            continue
        scored, conceded = _goals_for_team(m, home_id)
        if scored is None:
            continue
        if scored > conceded:
            results.append("W")
        elif scored == conceded:
            results.append("D")
        else:
            results.append("L")
        if len(results) >= 5:
            break
    return results
