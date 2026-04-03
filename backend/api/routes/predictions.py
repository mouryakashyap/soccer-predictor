from fastapi import APIRouter, HTTPException
from backend.data.store import get_fixtures, get_odds
from backend.models.predictor import predict, predict_all
from backend.models.value import calculate_value

router = APIRouter(prefix="/predictions", tags=["predictions"])


@router.get("")
def all_predictions():
    fixtures = get_fixtures()
    predictions = predict_all(fixtures)
    results = []
    for f, pred in zip(fixtures, predictions):
        odds = get_odds(f["fixture_id"])
        value_bets = calculate_value(pred, odds) if odds else []
        results.append({
            "fixture":     f,
            "predictions": {k: v for k, v in pred.items() if k not in ("features",)},
            "value_bets":  value_bets,
        })
    return results


@router.get("/{fixture_id}")
def fixture_prediction(fixture_id: str):
    fixtures = get_fixtures()
    fixture = next((f for f in fixtures if f["fixture_id"] == fixture_id), None)
    if not fixture:
        raise HTTPException(status_code=404, detail="Fixture not found")

    pred = predict(fixture)
    odds = get_odds(fixture_id)
    value_bets = calculate_value(pred, odds) if odds else []

    return {
        "fixture":     fixture,
        "predictions": {k: v for k, v in pred.items() if k not in ("features",)},
        "value_bets":  value_bets,
    }
