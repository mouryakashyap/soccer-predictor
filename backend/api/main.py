import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes import fixtures, predictions, parlays
from backend.config import USE_MOCK_DATA, USE_LLM_PREDICTOR


def _warm_cache():
    """
    Pre-fetch all data needed for predictions so the first HTTP request is instant.
    Runs in a background thread at startup (non-blocking).
    Only active in live mode — mock mode needs no warming.
    """
    if USE_MOCK_DATA:
        return
    try:
        from backend.data.fetchers.football_data import (
            fetch_upcoming_fixtures,
            fetch_competition_standings,
            fetch_season_matches,
        )
        fixtures_list = fetch_upcoming_fixtures()
        codes = list({f["competition_code"] for f in fixtures_list})
        for code in codes:
            fetch_competition_standings(code)
            fetch_season_matches(code)

    except Exception as e:
        print(f"[cache warm] warning: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    threading.Thread(target=_warm_cache, daemon=True).start()
    yield


app = FastAPI(title="Soccer Predictor API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:5175", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(fixtures.router)
app.include_router(predictions.router)
app.include_router(parlays.router)


@app.get("/health")
def health():
    return {"status": "ok"}
