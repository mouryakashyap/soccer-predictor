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
    # Build candidate picks: one pick per market per fixture (up to 3 per fixture).
    # This gives a much larger and more varied pool than one-pick-per-fixture,
    # which was the root cause of near-identical parlays.
    # The one-leg-per-fixture constraint is still enforced during combo building.
    candidate_picks: List[Dict] = []

    for pred in predictions:
        fixture_id = pred.get("fixture_id")
        if not fixture_id:
            continue

        fixture = fixture_map.get(fixture_id, {})

        for market, outcomes in _MARKETS:
            market_probs = pred.get(market)
            if not market_probs:
                continue

            best_outcome = max(outcomes, key=lambda o: market_probs.get(o, 0.0))
            best_prob = market_probs.get(best_outcome, 0.0)

            if best_prob < CONFIDENCE_THRESHOLD:
                continue

            candidate_picks.append({
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
            })

    if len(candidate_picks) < MIN_PARLAY_SIZE:
        return []

    # Cap candidates to avoid combinatorial explosion.
    # C(20, 7) ≈ 77K — fast. C(35, 7) ≈ 6.7M — too slow.
    MAX_CANDIDATES = 20
    N_PER_SIZE = 3
    MIN_UNIQUE_FIXTURES = 2
    # Each appearance of a fixture in a larger-size parlay reduces its effective
    # probability by this amount, pushing smaller sizes toward fresh fixtures.
    REUSE_PENALTY = 0.12

    def _fixture_set(parlay: Dict) -> set:
        return {leg["fixture_id"] for leg in parlay["legs"]}

    def _build_parlay(combo: tuple) -> Dict:
        combined_prob = 1.0
        for pick in combo:
            combined_prob *= pick["model_prob"]
        return {
            "size":           len(combo),
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
            "combined_prob":  round(combined_prob, 6),
            "combined_odds":  0.0,
            "expected_value": 0.0,
        }

    # Process from largest to smallest. Fixtures that appear in larger-size
    # parlays get a probability penalty so smaller sizes surface different combos.
    result: List[Dict] = []
    fixture_usage: Dict[str, int] = {}  # fixture_id → appearances in larger parlays

    for size in range(MAX_PARLAY_SIZE, MIN_PARLAY_SIZE - 1, -1):
        # Re-rank candidates: penalize heavily reused fixtures
        def _effective_prob(pick: Dict) -> float:
            penalty = fixture_usage.get(pick["fixture_id"], 0) * REUSE_PENALTY
            return max(pick["model_prob"] - penalty, 0.01)

        scored = sorted(candidate_picks, key=_effective_prob, reverse=True)[:MAX_CANDIDATES]

        if len(scored) < size:
            continue

        # Generate all valid combos for this size
        size_parlays: List[Dict] = []
        for combo in combinations(scored, size):
            fids = [p["fixture_id"] for p in combo]
            if len(fids) != len(set(fids)):
                continue
            parlay = _build_parlay(combo)
            if parlay["combined_prob"] < MIN_PARLAY_PROB:
                continue
            size_parlays.append(parlay)

        # Sort by true combined_prob (not penalized) and select diverse set
        size_parlays.sort(key=lambda p: p["combined_prob"], reverse=True)
        selected: List[Dict] = []
        selected_fsets: List[set] = []
        for candidate in size_parlays:
            cset = _fixture_set(candidate)
            diverse = all(
                len(cset.symmetric_difference(s)) >= MIN_UNIQUE_FIXTURES * 2
                for s in selected_fsets
            )
            if diverse:
                selected.append(candidate)
                selected_fsets.append(cset)
            if len(selected) >= N_PER_SIZE:
                break

        result.extend(selected)

        # Penalize selected fixtures so smaller sizes are pushed to use others
        for parlay in selected:
            for leg in parlay["legs"]:
                fid = leg["fixture_id"]
                fixture_usage[fid] = fixture_usage.get(fid, 0) + 1

    result.sort(key=lambda p: (p["size"], -p["combined_prob"]))
    return result
