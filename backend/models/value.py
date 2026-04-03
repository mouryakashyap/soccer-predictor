"""
Value calculator: compares model probabilities against bookmaker implied probabilities.
A bet has value when model_prob > implied_prob by at least VALUE_THRESHOLD.
"""
from typing import Dict, List
from backend.config import VALUE_THRESHOLD


def implied_prob(decimal_odds: float) -> float:
    if decimal_odds <= 0:
        return 1.0
    return round(1 / decimal_odds, 4)


def calculate_value(predictions: Dict, odds: Dict) -> List[Dict]:
    """
    Cross-references model predictions with bookmaker odds.
    Returns a flat list of value bets across all markets.

    Each item: {fixture_id, market, outcome, model_prob, implied_prob, edge, decimal_odds}
    """
    value_bets = []
    fixture_id = predictions["fixture_id"]

    market_map = {
        "h2h":    {"home_win": "home", "draw": "draw", "away_win": "away"},
        "totals": {"over_2_5": "over", "under_2_5": "under"},
        "btts":   {"yes": "yes", "no": "no"},
    }

    for market, outcome_map in market_map.items():
        if market not in odds or market not in predictions:
            continue
        for model_key, odds_key in outcome_map.items():
            model_prob = predictions[market].get(model_key)
            decimal = odds[market].get(odds_key)
            if model_prob is None or decimal is None:
                continue

            imp = implied_prob(decimal)
            edge = round(model_prob - imp, 4)

            value_bets.append({
                "fixture_id":   fixture_id,
                "market":       market,
                "outcome":      model_key,
                "model_prob":   model_prob,
                "implied_prob": imp,
                "edge":         edge,
                "decimal_odds": decimal,
                "is_value":     edge >= VALUE_THRESHOLD,
            })

    return value_bets
