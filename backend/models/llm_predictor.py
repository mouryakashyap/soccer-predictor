"""
LLM-based probability predictor using OpenAI.

Uses function-calling (structured output) to guarantee the app's JSON schema.
Batches up to LLM_BATCH_SIZE fixtures per API call to reduce latency/cost.
Falls back to rule-based predictor on any API or parsing error.
"""
import json
import logging
import time
from typing import Dict, List, Optional

from openai import OpenAI

from backend.config import OPENAI_API_KEY, LLM_MODEL, LLM_BATCH_SIZE, LLM_CACHE_TTL_SECONDS
from backend.models.features import build_features
from backend.data.store import get_team_stats, get_h2h

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# In-memory TTL cache: fixture_id -> (timestamp, prediction_dict)
# ---------------------------------------------------------------------------
_cache: Dict[str, tuple] = {}


def _cache_get(fixture_id: str) -> Optional[Dict]:
    entry = _cache.get(fixture_id)
    if entry and (time.time() - entry[0]) < LLM_CACHE_TTL_SECONDS:
        return entry[1]
    return None


def _cache_set(fixture_id: str, prediction: Dict):
    _cache[fixture_id] = (time.time(), prediction)


# ---------------------------------------------------------------------------
# Function schema — OpenAI function calling enforces the output shape
# ---------------------------------------------------------------------------
PREDICTION_FUNCTION = {
    "name": "submit_predictions",
    "description": (
        "Submit match probability predictions for one or more fixtures. "
        "Each prediction covers 1X2 result, over/under 2.5 goals, and BTTS markets. "
        "All probability pairs/triples must sum to 1.0."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "predictions": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "fixture_id": {"type": "string"},
                        "h2h": {
                            "type": "object",
                            "properties": {
                                "home_win": {"type": "number"},
                                "draw":     {"type": "number"},
                                "away_win": {"type": "number"},
                            },
                            "required": ["home_win", "draw", "away_win"],
                        },
                        "totals": {
                            "type": "object",
                            "properties": {
                                "over_2_5":  {"type": "number"},
                                "under_2_5": {"type": "number"},
                            },
                            "required": ["over_2_5", "under_2_5"],
                        },
                        "btts": {
                            "type": "object",
                            "properties": {
                                "yes": {"type": "number"},
                                "no":  {"type": "number"},
                            },
                            "required": ["yes", "no"],
                        },
                    },
                    "required": ["fixture_id", "h2h", "totals", "btts"],
                },
            }
        },
        "required": ["predictions"],
    },
}

SYSTEM_PROMPT = """You are an expert soccer analyst and probability estimator.

For each fixture provided, estimate realistic match probabilities for three markets:
1. **1X2**: home_win, draw, away_win (must sum to 1.0)
2. **Over/Under 2.5 goals**: over_2_5, under_2_5 (must sum to 1.0)
3. **BTTS (Both Teams To Score)**: yes, no (must sum to 1.0)

Calibration guidelines:
- Average home win rate in top leagues ~45%, draw ~27%, away ~28%. Adjust from there.
- Even a massive favourite rarely exceeds 85-90% win probability. Draws always possible.
- For BTTS: a dominant team with a high clean sheet rate (0.5+) may score 3 goals while keeping a clean sheet. High goals scored does NOT mean high BTTS. Weight clean sheet rates heavily.
- For O/U 2.5: use both teams' attack AND defence. Low-scoring defences push toward under.
- H2H with only 1-2 matches is a weak signal. Don't let it dominate.
- Probabilities must be between 0.01 and 0.99.

Reason step by step about each fixture before calling the function."""


def _build_briefing(fixture: Dict, home_stats: Dict, away_stats: Dict,
                    h2h: list, features: Dict) -> str:
    return "\n".join([
        f"## Fixture ID: {fixture['fixture_id']}",
        f"{fixture['home_team']} (Home) vs {fixture['away_team']} (Away)",
        f"League: {fixture.get('league', '?')}  |  Date: {fixture.get('kickoff', '?')[:10]}",
        "",
        f"### {fixture['home_team']}",
        f"- Position: {home_stats.get('league_position', '?')}",
        f"- Goals scored avg: {home_stats.get('goals_scored_avg', '?')}/game",
        f"- Goals conceded avg: {home_stats.get('goals_conceded_avg', '?')}/game",
        f"- Last 5: {', '.join(home_stats.get('last_5', []))}",
        f"- BTTS rate: {home_stats.get('btts_rate', '?')}  Clean sheet rate: {home_stats.get('clean_sheet_rate', '?')}",
        "",
        f"### {fixture['away_team']}",
        f"- Position: {away_stats.get('league_position', '?')}",
        f"- Goals scored avg: {away_stats.get('goals_scored_avg', '?')}/game",
        f"- Goals conceded avg: {away_stats.get('goals_conceded_avg', '?')}/game",
        f"- Last 5: {', '.join(away_stats.get('last_5', []))}",
        f"- BTTS rate: {away_stats.get('btts_rate', '?')}  Clean sheet rate: {away_stats.get('clean_sheet_rate', '?')}",
        "",
        f"### H2H (this season, home team perspective)",
        f"- Results: {', '.join(h2h) if h2h else 'none yet'}  (sample: {len(h2h)})",
        "",
        f"### Key computed features",
        f"- Form delta (home - away): {features['form_delta']:.3f}",
        f"- Position delta (away_pos - home_pos): {features['position_delta']}",
        f"- Defense-adjusted xG home: {round((features['home_goals_scored'] + features['away_goals_conceded'])/2, 2)}",
        f"- Defense-adjusted xG away: {round((features['away_goals_scored'] + features['home_goals_conceded'])/2, 2)}",
    ])


# ---------------------------------------------------------------------------
# LLM call
# ---------------------------------------------------------------------------
def _call_llm_batch(briefings: List[Dict]) -> List[Dict]:
    """Send a batch of briefings to OpenAI, return normalized predictions."""
    combined = "# Match Briefings\n\n" + "\n\n---\n\n".join(
        b["briefing_text"] for b in briefings
    )
    combined += f"\n\nAnalyse all {len(briefings)} fixture(s) and call submit_predictions."

    client = OpenAI(api_key=OPENAI_API_KEY)
    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": combined},
        ],
        functions=[PREDICTION_FUNCTION],
        function_call={"name": "submit_predictions"},
        temperature=0.2,
    )

    call = response.choices[0].message.function_call
    if not call:
        raise ValueError("OpenAI response missing function_call")

    raw = json.loads(call.arguments)
    return _normalize(raw.get("predictions", []))


def _normalize(raw: List[Dict]) -> List[Dict]:
    """Clamp to [0.01, 0.99] and renormalize each market to sum to 1.0."""
    out = []
    for pred in raw:
        norm = {"fixture_id": pred["fixture_id"]}
        for market, keys in [
            ("h2h",    ["home_win", "draw", "away_win"]),
            ("totals", ["over_2_5", "under_2_5"]),
            ("btts",   ["yes", "no"]),
        ]:
            vals = {k: max(0.01, min(0.99, float(pred[market][k]))) for k in keys}
            total = sum(vals.values())
            norm[market] = {k: round(v / total, 4) for k, v in vals.items()}
        out.append(norm)
    return out


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def predict_single(fixture: Dict) -> Dict:
    cached = _cache_get(fixture["fixture_id"])
    if cached:
        return cached

    home_stats = get_team_stats(fixture["home_team"]) or {}
    away_stats  = get_team_stats(fixture["away_team"]) or {}
    h2h         = get_h2h(fixture["home_team"], fixture["away_team"])
    features    = build_features(home_stats, away_stats, h2h)

    preds = _call_llm_batch([{
        "fixture_id":    fixture["fixture_id"],
        "briefing_text": _build_briefing(fixture, home_stats, away_stats, h2h, features),
        "features":      features,
    }])

    if not preds:
        raise ValueError("No prediction returned")

    result = {**preds[0], "features": features}
    _cache_set(fixture["fixture_id"], result)
    return result


def predict_batch(fixtures: List[Dict]) -> List[Optional[Dict]]:
    results: Dict[str, Dict] = {}
    to_predict = []

    for fixture in fixtures:
        cached = _cache_get(fixture["fixture_id"])
        if cached:
            results[fixture["fixture_id"]] = cached
        else:
            home_stats = get_team_stats(fixture["home_team"]) or {}
            away_stats  = get_team_stats(fixture["away_team"]) or {}
            h2h         = get_h2h(fixture["home_team"], fixture["away_team"])
            features    = build_features(home_stats, away_stats, h2h)
            to_predict.append({
                "fixture_id":    fixture["fixture_id"],
                "briefing_text": _build_briefing(fixture, home_stats, away_stats, h2h, features),
                "features":      features,
            })

    for i in range(0, len(to_predict), LLM_BATCH_SIZE):
        batch = to_predict[i : i + LLM_BATCH_SIZE]
        try:
            preds = _call_llm_batch(batch)
            pred_map = {p["fixture_id"]: p for p in preds}
            for item in batch:
                fid = item["fixture_id"]
                if fid in pred_map:
                    pred_map[fid]["features"] = item["features"]
                    results[fid] = pred_map[fid]
                    _cache_set(fid, pred_map[fid])
                else:
                    logger.warning("LLM omitted fixture %s — rule-based fallback will apply", fid)
        except Exception as e:
            logger.error("LLM batch failed: %s", e)

    return [results.get(f["fixture_id"]) for f in fixtures]
