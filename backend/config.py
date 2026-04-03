import os
from datetime import datetime

API_FOOTBALL_KEY    = os.getenv("API_FOOTBALL_KEY", "")
FOOTBALL_DATA_KEY   = os.getenv("FOOTBALL_DATA_KEY", "")
ODDS_API_KEY        = os.getenv("ODDS_API_KEY", "")

# Season year (API-Football uses the year the season started).
# Auto-detects: Aug+ = current year, Jan-Jul = previous year.
_now = datetime.utcnow()
_auto_season = _now.year if _now.month >= 8 else _now.year - 1
CURRENT_SEASON = int(os.getenv("CURRENT_SEASON", str(_auto_season)))

USE_MOCK_DATA = os.getenv("USE_MOCK_DATA", "true").lower() == "true"

# --- LLM predictor settings ---
USE_LLM_PREDICTOR     = os.getenv("USE_LLM_PREDICTOR", "false").lower() == "true"
OPENAI_API_KEY        = os.getenv("OPENAI_API_KEY", "")
LLM_MODEL             = os.getenv("LLM_MODEL", "gpt-4o")
LLM_BATCH_SIZE        = int(os.getenv("LLM_BATCH_SIZE", "10"))
LLM_CACHE_TTL_SECONDS = int(os.getenv("LLM_CACHE_TTL_SECONDS", "3600"))

VALUE_THRESHOLD      = float(os.getenv("VALUE_THRESHOLD", "0.05"))
MIN_PARLAY_PROB      = float(os.getenv("MIN_PARLAY_PROB", "0.10"))
MAX_PARLAY_SIZE      = int(os.getenv("MAX_PARLAY_SIZE", "7"))
MIN_PARLAY_SIZE      = int(os.getenv("MIN_PARLAY_SIZE", "4"))
TOP_N_PARLAYS        = int(os.getenv("TOP_N_PARLAYS", "10"))
CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.55"))
