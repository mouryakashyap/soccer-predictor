from fastapi import APIRouter, Query
from backend.config import USE_LLM_PREDICTOR
from backend.data.store import get_fixtures, get_odds
from backend.models.predictor import predict, predict_all_cached
from backend.models.value import calculate_value
from backend.parlays.generator import generate_parlays, generate_confidence_parlays

router = APIRouter(prefix="/parlays", tags=["parlays"])


def _is_prediction_cache_warm() -> bool:
    """Return True if we have at least some cached predictions to work with."""
    if not USE_LLM_PREDICTOR:
        return True  # Rule-based is always instant
    from backend.models.llm_predictor import _cache
    return bool(_cache)


@router.get("")
def get_parlays(
    size: int = Query(default=None, description="Exact parlay size (legs). Omit for all sizes."),
    min_ev: float = Query(default=0.0, description="Minimum expected value filter"),
):
    # If LLM cache is cold (background warm-up still running), return empty
    # immediately rather than blocking on fixture/prediction fetches.
    if not _is_prediction_cache_warm():
        return []

    fixtures = get_fixtures()
    if not fixtures:
        return []

    fixture_map = {f["fixture_id"]: f for f in fixtures}

    # --- EV-based path: requires bookmaker odds ---
    all_value_bets = []
    for f in fixtures:
        odds = get_odds(f["fixture_id"])
        if not odds:
            continue
        pred = predict(f)
        value_bets = calculate_value(pred, odds)
        all_value_bets.extend(value_bets)

    parlays = generate_parlays(all_value_bets)

    # --- Confidence-based fallback: no odds available ---
    if not parlays:
        all_predictions = predict_all_cached(fixtures)
        if not all_predictions:
            return []
        parlays = generate_confidence_parlays(all_predictions, fixture_map)

        if size is not None:
            parlays = [p for p in parlays if p["size"] == size]
        if min_ev > 0:
            parlays = [p for p in parlays if p["expected_value"] >= min_ev]
        return parlays

    # --- Post-processing for EV parlays ---
    if size is not None:
        parlays = [p for p in parlays if p["size"] == size]

    if min_ev > 0:
        parlays = [p for p in parlays if p["expected_value"] >= min_ev]

    for parlay in parlays:
        for leg in parlay["legs"]:
            f = fixture_map.get(leg["fixture_id"])
            if not f:
                continue
            leg["home_team"] = f["home_team"]
            leg["away_team"] = f["away_team"]
            leg["league"]    = f["league"]
            leg["kickoff"]   = f["kickoff"]

    return parlays
