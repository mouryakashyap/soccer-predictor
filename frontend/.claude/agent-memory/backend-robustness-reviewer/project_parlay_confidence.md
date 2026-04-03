---
name: Parlay Confidence Fallback
description: Design decisions, trigger conditions, and known behaviors for confidence-based parlay generation
type: project
---

The confidence-based parlay fallback was implemented (as of 2026-04-02) and is fully wired end-to-end.

**Key design decisions:**

1. Fallback triggers when `generate_parlays(all_value_bets)` returns `[]` — this happens when:
   - No odds are available (`get_odds()` returns None for all fixtures — live mode with no ODDS_API_KEY)
   - Odds exist but no bet passes the `VALUE_THRESHOLD` edge threshold

2. In mock mode (`USE_MOCK_DATA=true`), all fixtures have odds in `ODDS` dict. EV-based parlays may or may not generate depending on model vs implied probability gap. Confidence fallback only activates if EV path yields nothing.

3. Confidence threshold is `CONFIDENCE_THRESHOLD = 0.55` (env-overridable). One pick per (fixture, market) — the highest-confidence outcome. One leg per fixture across all markets (enforced in combinations loop).

4. Sentinel values: when no odds available, legs return `decimal_odds: 0.0`, `edge: 0.0`, and parlays return `combined_odds: 0.0`, `expected_value: 0.0`. Frontend `Parlays.tsx` renders these as "0.00x" and "+0.0% EV" — not broken but visually misleading. Acceptable for now.

**Why:** Odds API key not configured; parlay page was showing empty. Confidence fallback ensures the page shows useful picks.

**How to apply:** When debugging empty parlays, check: (1) are odds returning from `get_odds()`? (2) are any value bets passing `is_value=True`? If both are no, the confidence path should activate. If confidence path also returns empty, check that CONFIDENCE_THRESHOLD (0.55) isn't too high for the model's output range.
