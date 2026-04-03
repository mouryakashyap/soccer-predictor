from fastapi import APIRouter
from backend.data.store import get_fixtures, get_odds

router = APIRouter(prefix="/fixtures", tags=["fixtures"])


@router.get("")
def list_fixtures():
    fixtures = get_fixtures()
    result = []
    for f in fixtures:
        odds = get_odds(f["fixture_id"])
        result.append({**f, "odds": odds})
    return result


@router.get("/{fixture_id}")
def get_fixture(fixture_id: str):
    fixtures = get_fixtures()
    for f in fixtures:
        if f["fixture_id"] == fixture_id:
            return {**f, "odds": get_odds(fixture_id)}
    return {"error": "fixture not found"}, 404
