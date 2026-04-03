"""
Mock fixtures, odds, and team stats for development/testing.
Replace with real fetchers by setting USE_MOCK_DATA=false in env.
"""
from datetime import datetime, timedelta

BASE_DATE = datetime.utcnow().replace(hour=15, minute=0, second=0, microsecond=0)


FIXTURES = [
    {
        "fixture_id": "f001",
        "home_team": "Manchester City",
        "away_team": "Arsenal",
        "kickoff": (BASE_DATE + timedelta(days=1)).isoformat(),
        "league": "Premier League",
        "season": 2025,
    },
    {
        "fixture_id": "f002",
        "home_team": "Real Madrid",
        "away_team": "Barcelona",
        "kickoff": (BASE_DATE + timedelta(days=1)).isoformat(),
        "league": "La Liga",
        "season": 2025,
    },
    {
        "fixture_id": "f003",
        "home_team": "Bayern Munich",
        "away_team": "Borussia Dortmund",
        "kickoff": (BASE_DATE + timedelta(days=2)).isoformat(),
        "league": "Bundesliga",
        "season": 2025,
    },
    {
        "fixture_id": "f004",
        "home_team": "PSG",
        "away_team": "Marseille",
        "kickoff": (BASE_DATE + timedelta(days=2)).isoformat(),
        "league": "Ligue 1",
        "season": 2025,
    },
    {
        "fixture_id": "f005",
        "home_team": "Inter Milan",
        "away_team": "AC Milan",
        "kickoff": (BASE_DATE + timedelta(days=3)).isoformat(),
        "league": "Serie A",
        "season": 2025,
    },
    {
        "fixture_id": "f006",
        "home_team": "Liverpool",
        "away_team": "Chelsea",
        "kickoff": (BASE_DATE + timedelta(days=3)).isoformat(),
        "league": "Premier League",
        "season": 2025,
    },
    {
        "fixture_id": "f007",
        "home_team": "Atletico Madrid",
        "away_team": "Sevilla",
        "kickoff": (BASE_DATE + timedelta(days=4)).isoformat(),
        "league": "La Liga",
        "season": 2025,
    },
]


# Decimal odds per fixture per market
# Markets: h2h (home/draw/away), totals (over2.5/under2.5), btts (yes/no)
ODDS = {
    "f001": {
        "h2h":    {"home": 2.10, "draw": 3.50, "away": 3.20},
        "totals": {"over": 1.80, "under": 2.05},
        "btts":   {"yes": 1.75, "no": 2.10},
    },
    "f002": {
        "h2h":    {"home": 2.40, "draw": 3.20, "away": 2.80},
        "totals": {"over": 1.65, "under": 2.30},
        "btts":   {"yes": 1.60, "no": 2.40},
    },
    "f003": {
        "h2h":    {"home": 1.75, "draw": 3.80, "away": 4.50},
        "totals": {"over": 1.72, "under": 2.15},
        "btts":   {"yes": 1.85, "no": 2.00},
    },
    "f004": {
        "h2h":    {"home": 1.55, "draw": 4.00, "away": 5.50},
        "totals": {"over": 1.70, "under": 2.20},
        "btts":   {"yes": 1.90, "no": 1.95},
    },
    "f005": {
        "h2h":    {"home": 2.20, "draw": 3.30, "away": 3.10},
        "totals": {"over": 1.85, "under": 2.00},
        "btts":   {"yes": 1.70, "no": 2.15},
    },
    "f006": {
        "h2h":    {"home": 2.05, "draw": 3.40, "away": 3.50},
        "totals": {"over": 1.75, "under": 2.10},
        "btts":   {"yes": 1.65, "no": 2.30},
    },
    "f007": {
        "h2h":    {"home": 1.90, "draw": 3.60, "away": 4.00},
        "totals": {"over": 2.00, "under": 1.85},
        "btts":   {"yes": 2.00, "no": 1.88},
    },
}


# Team stats used for feature engineering
# last_5: list of results W/D/L, goals_scored_avg, goals_conceded_avg, btts_rate, clean_sheet_rate
TEAM_STATS = {
    "Manchester City": {
        "last_5": ["W", "W", "W", "D", "W"],
        "goals_scored_avg": 2.8,
        "goals_conceded_avg": 0.9,
        "btts_rate": 0.55,
        "clean_sheet_rate": 0.50,
        "league_position": 1,
    },
    "Arsenal": {
        "last_5": ["W", "W", "D", "W", "L"],
        "goals_scored_avg": 2.2,
        "goals_conceded_avg": 1.1,
        "btts_rate": 0.60,
        "clean_sheet_rate": 0.35,
        "league_position": 2,
    },
    "Real Madrid": {
        "last_5": ["W", "D", "W", "W", "W"],
        "goals_scored_avg": 2.5,
        "goals_conceded_avg": 1.0,
        "btts_rate": 0.65,
        "clean_sheet_rate": 0.40,
        "league_position": 1,
    },
    "Barcelona": {
        "last_5": ["W", "W", "L", "W", "D"],
        "goals_scored_avg": 2.4,
        "goals_conceded_avg": 1.2,
        "btts_rate": 0.70,
        "clean_sheet_rate": 0.30,
        "league_position": 2,
    },
    "Bayern Munich": {
        "last_5": ["W", "W", "W", "W", "D"],
        "goals_scored_avg": 3.1,
        "goals_conceded_avg": 1.1,
        "btts_rate": 0.70,
        "clean_sheet_rate": 0.35,
        "league_position": 1,
    },
    "Borussia Dortmund": {
        "last_5": ["L", "W", "D", "W", "L"],
        "goals_scored_avg": 1.9,
        "goals_conceded_avg": 1.8,
        "btts_rate": 0.75,
        "clean_sheet_rate": 0.20,
        "league_position": 4,
    },
    "PSG": {
        "last_5": ["W", "W", "W", "D", "W"],
        "goals_scored_avg": 3.0,
        "goals_conceded_avg": 0.8,
        "btts_rate": 0.50,
        "clean_sheet_rate": 0.55,
        "league_position": 1,
    },
    "Marseille": {
        "last_5": ["D", "W", "L", "D", "W"],
        "goals_scored_avg": 1.6,
        "goals_conceded_avg": 1.5,
        "btts_rate": 0.60,
        "clean_sheet_rate": 0.30,
        "league_position": 3,
    },
    "Inter Milan": {
        "last_5": ["W", "W", "D", "W", "W"],
        "goals_scored_avg": 2.3,
        "goals_conceded_avg": 0.9,
        "btts_rate": 0.55,
        "clean_sheet_rate": 0.45,
        "league_position": 1,
    },
    "AC Milan": {
        "last_5": ["D", "W", "L", "W", "D"],
        "goals_scored_avg": 1.8,
        "goals_conceded_avg": 1.4,
        "btts_rate": 0.65,
        "clean_sheet_rate": 0.30,
        "league_position": 3,
    },
    "Liverpool": {
        "last_5": ["W", "W", "W", "L", "W"],
        "goals_scored_avg": 2.6,
        "goals_conceded_avg": 1.2,
        "btts_rate": 0.65,
        "clean_sheet_rate": 0.35,
        "league_position": 3,
    },
    "Chelsea": {
        "last_5": ["D", "W", "D", "W", "L"],
        "goals_scored_avg": 1.7,
        "goals_conceded_avg": 1.3,
        "btts_rate": 0.60,
        "clean_sheet_rate": 0.35,
        "league_position": 5,
    },
    "Atletico Madrid": {
        "last_5": ["W", "D", "W", "D", "W"],
        "goals_scored_avg": 1.8,
        "goals_conceded_avg": 0.7,
        "btts_rate": 0.40,
        "clean_sheet_rate": 0.55,
        "league_position": 3,
    },
    "Sevilla": {
        "last_5": ["L", "D", "W", "L", "D"],
        "goals_scored_avg": 1.3,
        "goals_conceded_avg": 1.5,
        "btts_rate": 0.55,
        "clean_sheet_rate": 0.25,
        "league_position": 7,
    },
}


# Head-to-head records: list of past results from home team perspective
H2H = {
    ("Manchester City", "Arsenal"):        ["W", "W", "D", "W", "L"],
    ("Real Madrid", "Barcelona"):          ["W", "D", "L", "W", "W"],
    ("Bayern Munich", "Borussia Dortmund"):["W", "W", "W", "D", "W"],
    ("PSG", "Marseille"):                  ["W", "W", "W", "W", "D"],
    ("Inter Milan", "AC Milan"):           ["D", "W", "L", "W", "D"],
    ("Liverpool", "Chelsea"):              ["W", "D", "W", "L", "W"],
    ("Atletico Madrid", "Sevilla"):        ["W", "W", "D", "W", "L"],
}
