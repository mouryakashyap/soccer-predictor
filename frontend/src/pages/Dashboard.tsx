import { useEffect, useMemo, useState } from "react";
import { getPredictions, type PredictionResult } from "../api/client";
import FixtureCard from "../components/FixtureCard";

// Canonical display order for the five supported leagues.
const LEAGUE_ORDER: Record<string, number> = {
  PL: 0, // Premier League
  PD: 1, // La Liga
  BL1: 2, // Bundesliga
  SA: 3, // Serie A
  FL1: 4, // Ligue 1
};

const LEAGUE_DISPLAY_NAMES: Record<string, string> = {
  PL: "Premier League",
  PD: "La Liga",
  BL1: "Bundesliga",
  SA: "Serie A",
  FL1: "Ligue 1",
};

// Per-league color tokens: [activeBg, activeText, activeBadge, inactiveBg, inactiveText, dotColor]
const LEAGUE_COLORS: Record<
  string,
  { active: string; inactive: string; badge: string; dot: string }
> = {
  PL: {
    active: "bg-purple-600 text-white shadow-sm",
    inactive: "bg-purple-50 text-purple-700 hover:bg-purple-100",
    badge: "bg-purple-500 text-white",
    dot: "bg-purple-500",
  },
  PD: {
    active: "bg-orange-500 text-white shadow-sm",
    inactive: "bg-orange-50 text-orange-700 hover:bg-orange-100",
    badge: "bg-orange-400 text-white",
    dot: "bg-orange-400",
  },
  BL1: {
    active: "bg-red-600 text-white shadow-sm",
    inactive: "bg-red-50 text-red-700 hover:bg-red-100",
    badge: "bg-red-500 text-white",
    dot: "bg-red-500",
  },
  SA: {
    active: "bg-blue-600 text-white shadow-sm",
    inactive: "bg-blue-50 text-blue-700 hover:bg-blue-100",
    badge: "bg-blue-500 text-white",
    dot: "bg-blue-500",
  },
  FL1: {
    active: "bg-emerald-600 text-white shadow-sm",
    inactive: "bg-emerald-50 text-emerald-700 hover:bg-emerald-100",
    badge: "bg-emerald-500 text-white",
    dot: "bg-emerald-500",
  },
};

function leagueSortKey(code: string): number {
  return LEAGUE_ORDER[code] ?? 99;
}

function kickoffDateKey(kickoff: string): string {
  return kickoff.slice(0, 10);
}

function formatDateHeading(dateKey: string): string {
  const date = new Date(`${dateKey}T00:00:00`);
  const todayKey = new Date().toLocaleDateString("en-CA"); // "YYYY-MM-DD" in local time
  const tomorrowDate = new Date();
  tomorrowDate.setDate(tomorrowDate.getDate() + 1);
  const tomorrowKey = tomorrowDate.toLocaleDateString("en-CA");

  const weekday = date.toLocaleDateString("en-GB", { weekday: "long" });
  const day = date.getDate();
  const month = date.toLocaleDateString("en-GB", { month: "short" });
  const base = `${weekday}, ${day} ${month}`;

  if (dateKey === todayKey) return `${base} · Today`;
  if (dateKey === tomorrowKey) return `${base} · Tomorrow`;
  return base;
}

function isToday(dateKey: string): boolean {
  return dateKey === new Date().toLocaleDateString("en-CA");
}

interface LeagueGroup {
  competitionCode: string;
  leagueName: string;
  fixtures: PredictionResult[];
}

interface DateGroup {
  dateKey: string;
  heading: string;
  leagueGroups: LeagueGroup[];
  totalFixtures: number;
}

function groupByDateThenLeague(results: PredictionResult[]): DateGroup[] {
  const dateMap = new Map<string, Map<string, LeagueGroup>>();

  for (const r of results) {
    const { league, competition_code, kickoff } = r.fixture;
    const dateKey = kickoffDateKey(kickoff);

    if (!dateMap.has(dateKey)) dateMap.set(dateKey, new Map());
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

  const sortedDateKeys = [...dateMap.keys()].sort();

  return sortedDateKeys.map((dateKey) => {
    const leagueMap = dateMap.get(dateKey)!;

    const leagueGroups = [...leagueMap.values()]
      .sort(
        (a, b) =>
          leagueSortKey(a.competitionCode) - leagueSortKey(b.competitionCode),
      )
      .map((group) => ({
        ...group,
        fixtures: [...group.fixtures].sort((a, b) =>
          a.fixture.kickoff.localeCompare(b.fixture.kickoff),
        ),
      }));

    const totalFixtures = leagueGroups.reduce(
      (s, g) => s + g.fixtures.length,
      0,
    );

    return {
      dateKey,
      heading: formatDateHeading(dateKey),
      leagueGroups,
      totalFixtures,
    };
  });
}

function DashboardSkeleton() {
  return (
    <div className="space-y-8 animate-pulse">
      {[...Array(2)].map((_, d) => (
        <div key={d} className="space-y-5">
          {/* Date heading */}
          <div className="flex items-center gap-3">
            <div className="h-5 bg-gray-200 rounded w-44" />
            <div className="flex-1 h-px bg-gray-100" />
            <div className="h-4 bg-gray-100 rounded w-16" />
          </div>
          {/* Cards */}
          {[...Array(d === 0 ? 3 : 2)].map((_, i) => (
            <div
              key={i}
              className="bg-white rounded-xl border border-gray-100 p-5 space-y-4"
            >
              <div className="flex justify-between">
                <div className="space-y-1.5">
                  <div className="h-4 bg-gray-200 rounded w-52" />
                  <div className="h-3 bg-gray-100 rounded w-20" />
                </div>
                <div className="h-6 bg-gray-100 rounded-full w-24" />
              </div>
              <div className="grid grid-cols-3 gap-2.5">
                {[...Array(3)].map((_, j) => (
                  <div key={j} className="bg-gray-50 rounded-lg p-3 space-y-2">
                    <div className="h-3 bg-gray-200 rounded w-10" />
                    {[...Array(3)].map((_, k) => (
                      <div key={k} className="h-3 bg-gray-100 rounded" />
                    ))}
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      ))}
    </div>
  );
}

export default function Dashboard() {
  const [results, setResults] = useState<PredictionResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [leagueFilter, setLeagueFilter] = useState<string | undefined>();

  useEffect(() => {
    getPredictions()
      .then(setResults)
      .catch(() => setError("Failed to load predictions"))
      .finally(() => setLoading(false));
  }, []);

  const allDateGroups = useMemo(
    () => groupByDateThenLeague(results),
    [results],
  );

  // Available leagues in canonical order, with per-league fixture counts
  const availableLeagues = useMemo(() => {
    const counts: Record<string, number> = {};
    for (const r of results) {
      counts[r.fixture.competition_code] =
        (counts[r.fixture.competition_code] ?? 0) + 1;
    }
    return Object.entries(counts)
      .sort(([a], [b]) => leagueSortKey(a) - leagueSortKey(b))
      .map(([code, count]) => ({
        code,
        label: LEAGUE_DISPLAY_NAMES[code] ?? code,
        count,
      }));
  }, [results]);

  // Apply league filter client-side; keep date grouping, drop empty date sections
  const dateGroups = useMemo(() => {
    if (!leagueFilter) return allDateGroups;
    return allDateGroups
      .map((dg) => {
        const leagueGroups = dg.leagueGroups.filter(
          (lg) => lg.competitionCode === leagueFilter,
        );
        const totalFixtures = leagueGroups.reduce(
          (s, g) => s + g.fixtures.length,
          0,
        );
        return { ...dg, leagueGroups, totalFixtures };
      })
      .filter((dg) => dg.leagueGroups.length > 0);
  }, [allDateGroups, leagueFilter]);

  const totalValueBets = useMemo(
    () =>
      results.reduce(
        (sum, r) => sum + r.value_bets.filter((b) => b.is_value).length,
        0,
      ),
    [results],
  );

  return (
    <div className="space-y-8">
      {/* Page header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            Upcoming Fixtures
          </h1>
          <p className="text-gray-500 text-sm mt-1">
            Pre-match predictions with value analysis
          </p>
        </div>
        {!loading && !error && results.length > 0 && (
          <div className="flex items-center gap-4">
            <div className="text-right">
              <div className="text-2xl font-bold text-gray-900">
                {results.length}
              </div>
              <div className="text-xs text-gray-400">fixtures</div>
            </div>
            {totalValueBets > 0 && (
              <div className="text-right border-l border-gray-200 pl-4">
                <div className="text-2xl font-bold text-emerald-600">
                  {totalValueBets}
                </div>
                <div className="text-xs text-gray-400">value bets</div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* League filter — only shown once data is loaded and there are multiple leagues */}
      {!loading && !error && availableLeagues.length > 1 && (
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-xs text-gray-400 font-medium shrink-0">
            League:
          </span>
          <button
            onClick={() => setLeagueFilter(undefined)}
            className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
              !leagueFilter
                ? "bg-indigo-600 text-white shadow-sm"
                : "bg-gray-100 text-gray-600 hover:bg-gray-200"
            }`}
          >
            All
          </button>
          {availableLeagues.map(({ code, label, count }) => {
            const colors = LEAGUE_COLORS[code];
            const active = leagueFilter === code;
            return (
              <button
                key={code}
                onClick={() => setLeagueFilter(active ? undefined : code)}
                title={label}
                className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors flex items-center gap-1.5 ${
                  active ? colors.active : colors.inactive
                }`}
              >
                {code}
                <span
                  className={`text-xs rounded-full px-1.5 py-px font-semibold ${
                    active ? colors.badge : "bg-white/40 text-current"
                  }`}
                >
                  {count}
                </span>
              </button>
            );
          })}
        </div>
      )}

      {loading && <DashboardSkeleton />}

      {/* Error state */}
      {error && (
        <div className="flex items-start gap-3 bg-red-50 border border-red-200 text-red-700 rounded-xl p-4">
          <svg
            className="w-5 h-5 mt-0.5 shrink-0"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M12 9v3m0 3h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"
            />
          </svg>
          <div>
            <div className="font-semibold text-sm">
              Unable to load predictions
            </div>
            <div className="text-xs mt-0.5 text-red-500">
              Make sure the backend is running on port 8000
            </div>
          </div>
        </div>
      )}

      {/* Empty state */}
      {!loading && !error && results.length === 0 && (
        <div className="text-center py-20">
          <div className="text-4xl mb-3">⚽</div>
          <div className="text-gray-700 font-semibold">
            No fixtures available
          </div>
          <div className="text-gray-400 text-sm mt-1">
            Check back closer to matchday
          </div>
        </div>
      )}

      {/* Date sections */}
      {!loading &&
        !error &&
        dateGroups.map((dateGroup) => (
          <section
            key={dateGroup.dateKey}
            aria-labelledby={`date-${dateGroup.dateKey}`}
          >
            {/* Date heading */}
            <div className="flex items-center gap-3 mb-5">
              <h2
                id={`date-${dateGroup.dateKey}`}
                className={`text-base font-bold shrink-0 ${
                  isToday(dateGroup.dateKey)
                    ? "text-indigo-700"
                    : "text-gray-800"
                }`}
              >
                {dateGroup.heading}
              </h2>
              <div className="flex-1 h-px bg-gray-200" aria-hidden="true" />
              <span className="text-xs text-gray-400 shrink-0 tabular-nums">
                {dateGroup.totalFixtures} match
                {dateGroup.totalFixtures !== 1 ? "es" : ""}
              </span>
            </div>

            <div className="space-y-6">
              {dateGroup.leagueGroups.map((leagueGroup) => (
                <div key={leagueGroup.competitionCode}>
                  {/* League sub-header */}
                  {(() => {
                    const colors = LEAGUE_COLORS[leagueGroup.competitionCode];
                    return (
                      <div className="flex items-center gap-2 mb-3">
                        {colors && (
                          <span
                            className={`inline-block w-2 h-2 rounded-full ${colors.dot}`}
                          />
                        )}
                        <p className="text-xs font-semibold uppercase tracking-widest text-gray-500">
                          {leagueGroup.leagueName}
                        </p>
                        <span className="text-xs text-gray-300">
                          {leagueGroup.fixtures.length}
                        </span>
                      </div>
                    );
                  })()}

                  <div className="space-y-3">
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
