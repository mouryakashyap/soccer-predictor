"""
The Odds API v4 fetcher (https://api.the-odds-api.com/v4).

Fetches h2h, totals (2.5 line), and BTTS markets from EU-region bookmakers.
Uses best available odds across the configured bookmakers (sharp books first).

Rate limits (free tier): 500 requests/month — we fetch all sports in one call
per sport key and cache aggressively.
"""
import httpx
from typing import Dict, List, Optional, Tuple

from backend.config import ODDS_API_KEY
from backend.data.cache import ttl_cache

BASE_URL = "https://api.the-odds-api.com/v4"

SPORT_KEYS = [
    "soccer_epl",
    "soccer_spain_la_liga",
    "soccer_germany_bundesliga",
    "soccer_france_ligue_one",
    "soccer_italy_serie_a",
]

# Prefer sharp/efficient books; fall back to whatever is available
PREFERRED_BOOKS = ["pinnacle", "betfair_ex_eu", "bet365", "betway", "unibet_eu"]


def _normalize(name: str) -> str:
    """Lowercase + strip for fuzzy team name matching between APIs."""
    return name.lower().strip()


# ---------------------------------------------------------------------------
# Internal parsers
# ---------------------------------------------------------------------------

def _best_h2h(bookmakers: List[Dict], home_team: str, away_team: str) -> Optional[Dict]:
    best: Dict[str, float] = {}
    for bm in bookmakers:
        for market in bm.get("markets", []):
            if market["key"] != "h2h":
                continue
            for outcome in market.get("outcomes", []):
                name = outcome["name"]
                price = float(outcome["price"])
                if name == home_team:
                    best["home"] = max(best.get("home", 0.0), price)
                elif name == "Draw":
                    best["draw"] = max(best.get("draw", 0.0), price)
                elif name == away_team:
                    best["away"] = max(best.get("away", 0.0), price)
    if len(best) == 3:
        return best
    return None


def _best_totals(bookmakers: List[Dict], line: str = "2.5") -> Optional[Dict]:
    over = under = 0.0
    for bm in bookmakers:
        for market in bm.get("markets", []):
            if market["key"] != "totals":
                continue
            for outcome in market.get("outcomes", []):
                point = str(outcome.get("point", outcome.get("description", "")))
                if point != line:
                    continue
                price = float(outcome["price"])
                if outcome["name"] == "Over":
                    over = max(over, price)
                elif outcome["name"] == "Under":
                    under = max(under, price)
    if over and under:
        return {"over": over, "under": under}
    return None


def _best_btts(bookmakers: List[Dict]) -> Optional[Dict]:
    yes = no = 0.0
    for bm in bookmakers:
        for market in bm.get("markets", []):
            if market["key"] != "btts":
                continue
            for outcome in market.get("outcomes", []):
                price = float(outcome["price"])
                name = outcome["name"].lower()
                if name == "yes":
                    yes = max(yes, price)
                elif name == "no":
                    no = max(no, price)
    if yes and no:
        return {"yes": yes, "no": no}
    return None


def _parse_event(event: Dict) -> Tuple[Tuple[str, str], Dict]:
    """Parse one event into (matchup_key, odds_dict)."""
    home = event["home_team"]
    away = event["away_team"]
    bms  = event.get("bookmakers", [])

    odds: Dict = {}
    h2h_odds = _best_h2h(bms, home, away)
    if h2h_odds:
        odds["h2h"] = h2h_odds
    totals = _best_totals(bms)
    if totals:
        odds["totals"] = totals
    btts = _best_btts(bms)
    if btts:
        odds["btts"] = btts

    key = (_normalize(home), _normalize(away))
    return key, odds


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

@ttl_cache(seconds=900)   # 15 min — odds change frequently
def fetch_all_odds() -> Dict[Tuple[str, str], Dict]:
    """
    Returns {(normalized_home, normalized_away): odds_dict} for all supported leagues.
    Silently skips any sport/market that returns a non-200 (e.g. not available on free tier).
    """
    all_odds: Dict[Tuple[str, str], Dict] = {}
    for sport in SPORT_KEYS:
        try:
            resp = httpx.get(
                f"{BASE_URL}/sports/{sport}/odds",
                params={
                    "apiKey":      ODDS_API_KEY,
                    "regions":     "eu",
                    "markets":     "h2h,totals,btts",
                    "oddsFormat":  "decimal",
                    "bookmakers":  ",".join(PREFERRED_BOOKS),
                },
                timeout=10,
            )
            if resp.status_code in (422, 404):
                continue
            resp.raise_for_status()
            for event in resp.json():
                key, odds = _parse_event(event)
                if odds:
                    all_odds[key] = odds
        except httpx.HTTPError:
            continue   # don't crash if one sport fails
    return all_odds


def match_odds_to_fixture(fixture: Dict, all_odds: Dict[Tuple[str, str], Dict]) -> Dict:
    """
    Looks up odds for a fixture using normalised team names.
    Returns empty dict if no match found.
    """
    key = (_normalize(fixture["home_team"]), _normalize(fixture["away_team"]))
    return all_odds.get(key, {})
