---
name: Fixture interface additions
description: competition_code (string) and optional home_team_id/away_team_id (number) added to the Fixture interface in client.ts
type: project
---

The `Fixture` interface in `src/api/client.ts` was missing `competition_code`, `home_team_id`, and `away_team_id` fields that the backend actually returns. These were added to match the real API shape as described in the task.

**Why:** The backend `/predictions` response includes these fields; they are needed for league-section sorting logic and are part of the canonical API contract.

**How to apply:** `competition_code` is always present. `home_team_id` and `away_team_id` are typed as optional (`number | undefined`) in case older fixture records omit them.
