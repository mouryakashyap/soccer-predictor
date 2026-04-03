---
name: API Contract Notes
description: Backend response field names vs client.ts TypeScript interface field names; mismatches to watch for
type: project
---

Source of truth for frontend types: `/Users/mouryakashyap/SystemDesign/soccer-predictor/frontend/src/api/client.ts`

**Parlay / ParlayLeg field mapping (backend → frontend):**
- `size` → `Parlay.size` (NOT `num_legs`)
- `combined_prob` → `Parlay.combined_prob` (NOT `combined_probability`)
- `combined_odds` → `Parlay.combined_odds`
- `expected_value` → `Parlay.expected_value`
- `outcome` → `ParlayLeg.outcome` (NOT `selection`)
- `model_prob` → `ParlayLeg.model_prob` (NOT `probability`)
- `decimal_odds` → `ParlayLeg.decimal_odds`
- `edge` → `ParlayLeg.edge`

The task spec (2026-04-02) described a different shape (`combined_probability`, `num_legs`, `selection`, `probability`) — that is the desired REST API shape described in the task but NOT what client.ts expects. Backend must match client.ts, not the task description shape.

**ValueBet field mapping:**
- `is_value` must be a boolean (not 0/1 integer) — currently correct in value.py
- `implied_prob`, `edge`, `model_prob`, `decimal_odds` must be floats — correct

**Mock data notes:**
- Fixtures in mock_data.py do NOT have `competition_code`, `home_team_id`, or `away_team_id` fields
- `client.ts` Fixture interface marks these as optional (`competition_code: string`, `home_team_id?: number`) — frontend handles missing values gracefully
