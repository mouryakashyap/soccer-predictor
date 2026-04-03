---
name: LLM Predictor Integration
description: Architecture decision to use Claude as primary predictor with rule-based fallback, implemented 2026-04-01
type: project
---

Replaced rule-based heuristics with Claude LLM predictor (2026-04-01).

Key files:
- `backend/models/llm_predictor.py` -- LLM prediction engine using tool-use for structured output
- `backend/models/predictor.py` -- dispatcher that routes to LLM or rule-based based on USE_LLM_PREDICTOR flag
- `backend/config.py` -- added USE_LLM_PREDICTOR, ANTHROPIC_API_KEY, LLM_MODEL, LLM_BATCH_SIZE, LLM_CACHE_TTL_SECONDS

**Why:** Rule-based model had known calibration issues (H2H binary swing from 1-match samples, BTTS broken for dominant teams, no draw calibration, no floor on form adjustment). LLM can reason about edge cases naturally.

**How to apply:** Feature flag USE_LLM_PREDICTOR=true enables LLM mode. Rule-based model is always the fallback. Batch prediction via predict_all() groups fixtures into LLM_BATCH_SIZE chunks to reduce API calls.
