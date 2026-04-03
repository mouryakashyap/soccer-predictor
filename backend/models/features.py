"""
Feature engineering: converts raw team stats + H2H into a numeric feature vector.
"""
from typing import Dict, Any


def _form_score(results: list[str]) -> float:
    """Convert W/D/L list → weighted score (recent = higher weight)."""
    weights = [0.35, 0.25, 0.20, 0.12, 0.08]
    points = {"W": 3, "D": 1, "L": 0}
    score = sum(points[r] * w for r, w in zip(results[:5], weights))
    return round(score / 3.0, 4)  # normalise to [0,1]


def _h2h_score(results: list[str]) -> float:
    """Home-team win rate from H2H results."""
    if not results:
        return 0.5
    wins = results.count("W")
    return round(wins / len(results), 4)


def build_features(home_stats: Dict[str, Any], away_stats: Dict[str, Any], h2h: list[str]) -> Dict[str, float]:
    """
    Returns a flat feature dict for a single fixture.
    Keys are stable — used directly by predictor.py.
    """
    home_form = _form_score(home_stats.get("last_5", []))
    away_form = _form_score(away_stats.get("last_5", []))

    avg_goals_total = (
        home_stats.get("goals_scored_avg", 1.5)
        + away_stats.get("goals_scored_avg", 1.5)
    )
    btts_likelihood = (
        home_stats.get("btts_rate", 0.5) + away_stats.get("btts_rate", 0.5)
    ) / 2

    position_delta = (
        away_stats.get("league_position", 10) - home_stats.get("league_position", 10)
    )

    return {
        "home_form":           home_form,
        "away_form":           away_form,
        "form_delta":          round(home_form - away_form, 4),
        "h2h_home_win_rate":   _h2h_score(h2h),
        "avg_goals_total":     round(avg_goals_total, 4),
        "home_goals_scored":   home_stats.get("goals_scored_avg", 1.5),
        "away_goals_scored":   away_stats.get("goals_scored_avg", 1.5),
        "home_goals_conceded": home_stats.get("goals_conceded_avg", 1.5),
        "away_goals_conceded": away_stats.get("goals_conceded_avg", 1.5),
        "btts_likelihood":     round(btts_likelihood, 4),
        "home_clean_sheet":    home_stats.get("clean_sheet_rate", 0.3),
        "away_clean_sheet":    away_stats.get("clean_sheet_rate", 0.3),
        "position_delta":      position_delta,
    }
