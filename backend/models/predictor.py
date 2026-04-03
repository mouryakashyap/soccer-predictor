"""
Prediction dispatcher.

Routes to LLM-based or rule-based predictor depending on config.
The rule-based model always serves as the fallback when the LLM is
unavailable or returns invalid output.

Output contract (unchanged):
  {
    fixture_id: str,
    h2h:    {home_win, draw, away_win},
    totals: {over_2_5, under_2_5},
    btts:   {yes, no},
    features: { ... },
    source: "llm" | "rule_based"
  }
"""
import logging
import math
from typing import Dict, List

from backend.models.features import build_features
from backend.data.store import get_team_stats, get_h2h
from backend.config import USE_LLM_PREDICTOR

logger = logging.getLogger(__name__)


# ===================================================================
# Rule-based predictor (original heuristics, kept as fallback)
# ===================================================================

def _clamp(v: float, lo=0.01, hi=0.99) -> float:
    return max(lo, min(hi, v))


def _poisson_cdf(lam: float, k: int) -> float:
    """P(X <= k) for Poisson(lam). Used for goals total markets."""
    return sum(
        (lam ** i) * math.exp(-lam) / math.factorial(i)
        for i in range(k + 1)
    )


def _predict_1x2(features: Dict) -> Dict[str, float]:
    base_home = 0.45
    form_adj = features["form_delta"] * 0.25
    h2h_adj = (features["h2h_home_win_rate"] - 0.5) * 0.15
    pos_adj = features["position_delta"] * 0.015

    p_home = _clamp(base_home + form_adj + h2h_adj + pos_adj)
    closeness = 1 - abs(features["form_delta"]) - abs(h2h_adj)
    p_draw = _clamp(0.27 * closeness)
    p_away = _clamp(1 - p_home - p_draw)

    total = p_home + p_draw + p_away
    return {
        "home_win": round(p_home / total, 4),
        "draw":     round(p_draw / total, 4),
        "away_win": round(p_away / total, 4),
    }


def _predict_totals(features: Dict) -> Dict[str, float]:
    xg_home = (features["home_goals_scored"] + features["away_goals_conceded"]) / 2
    xg_away = (features["away_goals_scored"] + features["home_goals_conceded"]) / 2
    total_xg = xg_home + xg_away
    p_over = _clamp(1 - _poisson_cdf(total_xg, 2))
    return {
        "over_2_5":  round(p_over, 4),
        "under_2_5": round(1 - p_over, 4),
    }


def _predict_btts(features: Dict) -> Dict[str, float]:
    p_yes = _clamp(
        features["btts_likelihood"]
        - features["home_clean_sheet"] * 0.3
        - features["away_clean_sheet"] * 0.3
        + 0.05
    )
    return {
        "yes": round(p_yes, 4),
        "no":  round(1 - p_yes, 4),
    }


def _predict_rule_based(fixture: Dict) -> Dict:
    """Original rule-based prediction."""
    home_stats = get_team_stats(fixture["home_team"]) or {}
    away_stats = get_team_stats(fixture["away_team"]) or {}
    h2h = get_h2h(fixture["home_team"], fixture["away_team"])
    features = build_features(home_stats, away_stats, h2h)

    return {
        "fixture_id": fixture["fixture_id"],
        "h2h":        _predict_1x2(features),
        "totals":     _predict_totals(features),
        "btts":       _predict_btts(features),
        "features":   features,
        "source":     "rule_based",
    }


# ===================================================================
# Public API
# ===================================================================

def predict(fixture: Dict) -> Dict:
    """
    Predict a single fixture. Uses LLM if enabled, falls back to rule-based.
    """
    if USE_LLM_PREDICTOR:
        try:
            from backend.models.llm_predictor import predict_single
            result = predict_single(fixture)
            result["source"] = "llm"
            return result
        except Exception as e:
            logger.warning(
                "LLM prediction failed for %s, falling back to rule-based: %s",
                fixture.get("fixture_id"), e,
            )
    return _predict_rule_based(fixture)


def predict_all_cached(fixtures: List[Dict]) -> List[Dict]:
    """
    Return predictions using only what's already in the LLM cache.
    Falls back to rule-based instantly for any fixture not yet cached.
    Never triggers a new LLM API call — safe to call from any route.
    Returns an empty list if the LLM is enabled but the cache is fully cold
    (avoids slow football-data.org API calls on every uncached fixture).
    """
    if USE_LLM_PREDICTOR:
        from backend.models.llm_predictor import _cache_get
        cached_results = []
        uncached_fixtures = []
        for fixture in fixtures:
            cached = _cache_get(fixture["fixture_id"])
            if cached:
                cached_results.append({**cached, "source": "llm"})
            else:
                uncached_fixtures.append(fixture)

        # Return only what's already cached — skip uncached fixtures entirely.
        # Calling rule-based for uncached fixtures would trigger slow API calls
        # (get_team_stats → fetch_season_matches) while the warm-up thread may
        # still be holding those cache locks.
        return cached_results

    return [_predict_rule_based(f) for f in fixtures]


def predict_all(fixtures: List[Dict]) -> List[Dict]:
    """
    Predict all fixtures. Uses batched LLM calls if enabled.
    Falls back to rule-based per-fixture when LLM returns None or fails.
    """
    if USE_LLM_PREDICTOR:
        try:
            from backend.models.llm_predictor import predict_batch
            llm_results = predict_batch(fixtures)
            final = []
            for fixture, llm_pred in zip(fixtures, llm_results):
                if llm_pred is not None:
                    llm_pred["source"] = "llm"
                    final.append(llm_pred)
                else:
                    logger.warning(
                        "LLM returned None for %s, using rule-based fallback",
                        fixture.get("fixture_id"),
                    )
                    final.append(_predict_rule_based(fixture))
            return final
        except Exception as e:
            logger.error("LLM batch prediction failed entirely: %s", e)

    # Full fallback: rule-based for everything
    return [_predict_rule_based(f) for f in fixtures]
