# Agent Memory Index

- [Project: vite-env.d.ts was missing](project_vite_env_missing.md) — `src/vite-env.d.ts` did not exist; added it to fix `ImportMeta.env` TS error blocking all builds
- [Project: Fixture type competition_code added](project_fixture_type.md) — `competition_code` and optional `home_team_id`/`away_team_id` added to `Fixture` interface in `client.ts`
- [Project: Dashboard league grouping](project_dashboard_league_grouping.md) — Dashboard now groups fixtures by `fixture.league`, sorted by `competition_code` using a canonical order map (PL, PD, BL1, SA, FL1)
