"""
Parlay generator: builds EV-ranked combinations from value bets.

Rules:
  - Only include bets where is_value=True
  - Max 1 selection per fixture in a parlay
  - Combo size: MIN_PARLAY_SIZE to MAX_PARLAY_SIZE
  - Rank by expected_value = combined_prob * combined_odds - 1
  - Drop parlays where combined_prob < MIN_PARLAY_PROB

Confidence fallback (when no odds are available):
  - Build candidate picks from all market outcomes whose model_prob >= CONFIDENCE_THRESHOLD
  - Apply the same one-leg-per-fixture and size constraints
  - Rank by combined_probability descending (no EV possible without odds)
  - expected_value / combined_odds are set to 0.0 as sentinel values
"""
from itertools import combinations
from typing import List, Dict
from backend.config import (
    MIN_PARLAY_PROB,
    MAX_PARLAY_SIZE,
    MIN_PARLAY_SIZE,
    TOP_N_PARLAYS,
    CONFIDENCE_THRESHOLD,
)


def generate_parlays(value_bets: List[Dict]) -> List[Dict]:
    """
    value_bets: flat list of bets from value.calculate_value() across all fixtures.
    Returns top N parlays sorted by expected_value descending.
    """
    bets = [b for b in value_bets if b["is_value"]]

    if len(bets) < MIN_PARLAY_SIZE:
        return []

    parlays = []

    for size in range(MIN_PARLAY_SIZE, min(MAX_PARLAY_SIZE, len(bets)) + 1):
        for combo in combinations(bets, size):
            # Enforce: max 1 selection per fixture
            fixture_ids = [b["fixture_id"] for b in combo]
            if len(fixture_ids) != len(set(fixture_ids)):
                continue

            combined_prob = 1.0
            combined_odds = 1.0
            for b in combo:
                combined_prob *= b["model_prob"]
                combined_odds *= b["decimal_odds"]

            combined_prob = round(combined_prob, 6)
            combined_odds = round(combined_odds, 4)

            if combined_prob < MIN_PARLAY_PROB:
                continue

            ev = round(combined_prob * combined_odds - 1, 4)

            parlays.append({
                "size":          size,
                "legs":          [
                    {
                        "fixture_id":   b["fixture_id"],
                        "market":       b["market"],
                        "outcome":      b["outcome"],
                        "model_prob":   b["model_prob"],
                        "decimal_odds": b["decimal_odds"],
                        "edge":         b["edge"],
                    }
                    for b in combo
                ],
                "combined_prob":  combined_prob,
                "combined_odds":  combined_odds,
                "expected_value": ev,
            })

    parlays.sort(key=lambda p: p["expected_value"], reverse=True)
    return parlays[:TOP_N_PARLAYS]


# ---------------------------------------------------------------------------
# Markets whose outcomes are mutually exclusive within a single fixture.
# For each market we list every (outcome_key, opposite_keys) pair so that
# we can pick only the single highest-confidence outcome per market per
# fixture, avoiding double-counting from the same market.
# ---------------------------------------------------------------------------
_MARKETS = [
    ("h2h",    ["home_win", "draw", "away_win"]),
    ("totals", ["over_2_5", "under_2_5"]),
    ("btts",   ["yes", "no"]),
]


def generate_confidence_parlays(
    predictions: List[Dict],
    fixture_map: Dict[str, Dict],
) -> List[Dict]:
    """
    Build parlays purely from high-confidence model picks when no odds are
    available.

    Args:
        predictions: list of prediction dicts as returned by predictor.predict().
                     Each dict must contain fixture_id, h2h, totals, btts.
        fixture_map: mapping of fixture_id -> fixture dict (for team names etc.).

    Returns top N parlays sorted by combined_probability descending.
    The returned shape is identical to generate_parlays() so the route layer
    can handle both interchangeably.  Fields without meaning when no odds
    exist (decimal_odds, edge, combined_odds, expected_value) are set to 0.0.
    """
    # Build candidate picks: one pick per fixture — the single highest-confidence
    # outcome across all markets, provided it clears CONFIDENCE_THRESHOLD.
    # One pick per fixture guarantees the one-leg-per-fixture constraint is
    # always satisfied and keeps the candidate pool small (≤ num fixtures),
    # which makes combination generation fast even for size-5 parlays.
    candidate_picks: List[Dict] = []

    for pred in predictions:
        fixture_id = pred.get("fixture_id")
        if not fixture_id:
            continue

        fixture = fixture_map.get(fixture_id, {})
        best_pick = None

        for market, outcomes in _MARKETS:
            market_probs = pred.get(market)
            if not market_probs:
                continue

            best_outcome = max(outcomes, key=lambda o: market_probs.get(o, 0.0))
            best_prob = market_probs.get(best_outcome, 0.0)

            if best_prob < CONFIDENCE_THRESHOLD:
                continue

            if best_pick is None or best_prob > best_pick["model_prob"]:
                best_pick = {
                    "fixture_id":   fixture_id,
                    "market":       market,
                    "outcome":      best_outcome,
                    "model_prob":   best_prob,
                    "decimal_odds": 0.0,
                    "edge":         0.0,
                    "home_team":    fixture.get("home_team", ""),
                    "away_team":    fixture.get("away_team", ""),
                    "league":       fixture.get("league", ""),
                    "kickoff":      fixture.get("kickoff", ""),
                }

        if best_pick:
            candidate_picks.append(best_pick)

    if len(candidate_picks) < MIN_PARLAY_SIZE:
        return []

    # Cap candidates to avoid combinatorial explosion.
    # C(20, 7) ≈ 77K combinations — fast.  C(35, 7) ≈ 6.7M — too slow.
    MAX_CANDIDATES = 20
    candidate_picks.sort(key=lambda p: p["model_prob"], reverse=True)
    candidate_picks = candidate_picks[:MAX_CANDIDATES]

    parlays: List[Dict] = []
    max_size = min(MAX_PARLAY_SIZE, len(candidate_picks))

    for size in range(MIN_PARLAY_SIZE, max_size + 1):
        for combo in combinations(candidate_picks, size):
            # Enforce: at most one leg per fixture across all markets
            fixture_ids = [pick["fixture_id"] for pick in combo]
            if len(fixture_ids) != len(set(fixture_ids)):
                continue

            combined_prob = 1.0
            for pick in combo:
                combined_prob *= pick["model_prob"]
            combined_prob = round(combined_prob, 6)

            if combined_prob < MIN_PARLAY_PROB:
                continue

            parlays.append({
                "size":           size,
                "legs":           [
                    {
                        "fixture_id":   pick["fixture_id"],
                        "market":       pick["market"],
                        "outcome":      pick["outcome"],
                        "model_prob":   pick["model_prob"],
                        "decimal_odds": pick["decimal_odds"],
                        "edge":         pick["edge"],
                        "home_team":    pick["home_team"],
                        "away_team":    pick["away_team"],
                        "league":       pick["league"],
                        "kickoff":      pick["kickoff"],
                    }
                    for pick in combo
                ],
                "combined_prob":  combined_prob,
                "combined_odds":  0.0,   # not computable without real odds
                "expected_value": 0.0,   # not computable without real odds
            })

    # Return top 3 per leg count so every size is represented,
    # ordered by size ascending, then confidence descending within each size.
    N_PER_SIZE = 3
    result: List[Dict] = []
    for size in range(MIN_PARLAY_SIZE, MAX_PARLAY_SIZE + 1):
        group = [p for p in parlays if p["size"] == size]
        group.sort(key=lambda p: p["combined_prob"], reverse=True)
        result.extend(group[:N_PER_SIZE])
    result.sort(key=lambda p: (p["size"], -p["combined_prob"]))
    return result
