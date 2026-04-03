---
name: Dashboard date+league grouping
description: Dashboard groups /predictions results by date first, then by league within each date, using a two-level structure
type: project
---

`src/pages/Dashboard.tsx` now uses a two-level grouping: date sections (ascending) containing league sub-groups (canonical order).

**Data structure:**
- `DateGroup { dateKey, heading, leagueGroups: LeagueGroup[] }`
- `LeagueGroup { competitionCode, leagueName, fixtures: PredictionResult[] }`
- Built by `groupByDateThenLeague()` using a `Map<dateKey, Map<competitionCode, LeagueGroup>>`

**Sorting:**
- Date sections: ascending by `YYYY-MM-DD` string sort on `fixture.kickoff.slice(0, 10)`
- Leagues within a date: `LEAGUE_ORDER` map (PL=0, PD=1, BL1=2, SA=3, FL1=4; unknowns = 99)
- Fixtures within a league+date: ascending by `fixture.kickoff` string compare

**Date heading format:** "Saturday, 5 Apr" — produced by `formatDateHeading()` which appends `T00:00:00` before constructing a `Date` to avoid timezone drift on the date portion.

**LEAGUE_DISPLAY_NAMES** map translates `competition_code` to friendly names (e.g. BL1 → "Bundesliga"). League names from the API are used as fallback for unknown codes.

**UI:**
- Date heading: `text-xl font-bold text-gray-900` with a trailing `<hr>` line
- League sub-header: `text-sm font-semibold uppercase tracking-wide text-gray-400`
- `useMemo` wraps both `dateGroups` and `totalValueBets`

**How to apply:** To add a new league, add its code to both `LEAGUE_ORDER` and `LEAGUE_DISPLAY_NAMES` in Dashboard.tsx.
