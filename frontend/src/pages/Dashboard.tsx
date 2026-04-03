import { useEffect, useMemo, useState } from "react";
import { getPredictions, type PredictionResult } from "../api/client";
import FixtureCard from "../components/FixtureCard";

// Canonical display order for the five supported leagues.
// Any competition_code not listed here will be appended after with a high sort key.
const LEAGUE_ORDER: Record<string, number> = {
  PL: 0,   // Premier League
  PD: 1,   // La Liga
  BL1: 2,  // Bundesliga
  SA: 3,   // Serie A
  FL1: 4,  // Ligue 1
};

const LEAGUE_DISPLAY_NAMES: Record<string, string> = {
  PL: "Premier League",
  PD: "La Liga",
  BL1: "Bundesliga",
  SA: "Serie A",
  FL1: "Ligue 1",
};

function leagueSortKey(code: string): number {
  return LEAGUE_ORDER[code] ?? 99;
}

// Extract "YYYY-MM-DD" date string from an ISO kickoff string.
// We parse only the date portion to avoid timezone drift — fixtures are stored
// in local match time so the date component is authoritative.
function kickoffDateKey(kickoff: string): string {
  return kickoff.slice(0, 10); // "2026-04-05"
}

// Format a "YYYY-MM-DD" key into "Saturday, 5 Apr"
function formatDateHeading(dateKey: string): string {
  // Append T00:00:00 to force local-time interpretation
  const date = new Date(`${dateKey}T00:00:00`);
  const weekday = date.toLocaleDateString("en-GB", { weekday: "long" });
  const day = date.getDate(); // no leading zero
  const month = date.toLocaleDateString("en-GB", { month: "short" });
  return `${weekday}, ${day} ${month}`;
}

interface LeagueGroup {
  competitionCode: string;
  leagueName: string;
  fixtures: PredictionResult[];
}

interface DateGroup {
  dateKey: string;      // "2026-04-05" — used for sorting and React key
  heading: string;      // "Saturday, 5 Apr" — displayed to the user
  leagueGroups: LeagueGroup[];
}

function groupByDateThenLeague(results: PredictionResult[]): DateGroup[] {
  // date key → (competition_code → LeagueGroup)
  const dateMap = new Map<string, Map<string, LeagueGroup>>();

  for (const r of results) {
    const { league, competition_code, kickoff } = r.fixture;
    const dateKey = kickoffDateKey(kickoff);

    if (!dateMap.has(dateKey)) {
      dateMap.set(dateKey, new Map());
    }
    const leagueMap = dateMap.get(dateKey)!;

    if (!leagueMap.has(competition_code)) {
      leagueMap.set(competition_code, {
        competitionCode: competition_code,
        leagueName: LEAGUE_DISPLAY_NAMES[competition_code] ?? league,
        fixtures: [],
      });
    }
    leagueMap.get(competition_code)!.fixtures.push(r);
  }

  // Sort date keys ascending, then build the final array
  const sortedDateKeys = [...dateMap.keys()].sort();

  return sortedDateKeys.map((dateKey) => {
    const leagueMap = dateMap.get(dateKey)!;

    // Sort league groups by canonical order; sort fixtures within each group by kickoff
    const leagueGroups = [...leagueMap.values()]
      .sort((a, b) => leagueSortKey(a.competitionCode) - leagueSortKey(b.competitionCode))
      .map((group) => ({
        ...group,
        fixtures: [...group.fixtures].sort((a, b) =>
          a.fixture.kickoff.localeCompare(b.fixture.kickoff)
        ),
      }));

    return {
      dateKey,
      heading: formatDateHeading(dateKey),
      leagueGroups,
    };
  });
}

export default function Dashboard() {
  const [results, setResults] = useState<PredictionResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getPredictions()
      .then(setResults)
      .catch(() => setError("Failed to load predictions"))
      .finally(() => setLoading(false));
  }, []);

  const dateGroups = useMemo(() => groupByDateThenLeague(results), [results]);

  const totalValueBets = useMemo(
    () => results.reduce((sum, r) => sum + r.value_bets.filter((b) => b.is_value).length, 0),
    [results]
  );

  return (
    <div className="space-y-8">
      {/* Page header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Upcoming Fixtures</h1>
          <p className="text-gray-500 text-sm mt-1">Pre-match predictions with value analysis</p>
        </div>
        {!loading && (
          <div className="text-right">
            <div className="text-2xl font-bold text-indigo-600">{totalValueBets}</div>
            <div className="text-xs text-gray-500">total value bets</div>
          </div>
        )}
      </div>

      {/* Loading state */}
      {loading && (
        <div className="text-center py-16 text-gray-400">Loading predictions...</div>
      )}

      {/* Error state */}
      {error && (
        <div className="bg-red-50 text-red-700 rounded-lg p-4">{error}</div>
      )}

      {/* Empty state */}
      {!loading && !error && results.length === 0 && (
        <div className="text-center py-16 text-gray-400">No fixtures available</div>
      )}

      {/* Date sections */}
      {!loading && !error && dateGroups.map((dateGroup) => (
        <section key={dateGroup.dateKey} aria-labelledby={`date-${dateGroup.dateKey}`}>
          {/* Date heading with full-width rule */}
          <div className="flex items-center gap-3 mb-5">
            <h2
              id={`date-${dateGroup.dateKey}`}
              className="text-xl font-bold text-gray-900 shrink-0"
            >
              {dateGroup.heading}
            </h2>
            <div className="flex-1 h-px bg-gray-200" aria-hidden="true" />
          </div>

          {/* League sub-groups within this date */}
          <div className="space-y-6">
            {dateGroup.leagueGroups.map((leagueGroup) => (
              <div key={leagueGroup.competitionCode}>
                {/* League sub-header */}
                <p className="text-sm font-semibold uppercase tracking-wide text-gray-400 mb-3">
                  {leagueGroup.leagueName}
                </p>

                {/* Fixture cards */}
                <div className="space-y-4">
                  {leagueGroup.fixtures.map((r) => (
                    <FixtureCard key={r.fixture.fixture_id} result={r} />
                  ))}
                </div>
              </div>
            ))}
          </div>
        </section>
      ))}
    </div>
  );
}
