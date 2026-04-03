import { useEffect, useMemo, useState } from "react";
import { getParlays, type Parlay, type ParlayLeg } from "../api/client";
import { OUTCOME_LABEL, MARKET_LABEL } from "../lib/labels";

function parseLegLabels(leg: ParlayLeg): { market: string; outcome: string } {
  return {
    market: MARKET_LABEL[leg.market] ?? leg.market,
    outcome: OUTCOME_LABEL[leg.outcome] ?? leg.outcome,
  };
}

function ProbBadge({ prob }: { prob: number }) {
  const pct = (prob * 100).toFixed(1);
  let cls = "bg-gray-100 text-gray-600";
  if (prob >= 0.7) cls = "bg-emerald-100 text-emerald-700";
  else if (prob >= 0.5) cls = "bg-amber-100 text-amber-700";
  return (
    <span className={`text-xs font-bold px-2 py-0.5 rounded-full tabular-nums ${cls}`}>
      {pct}%
    </span>
  );
}

function ParlaySkeleton() {
  return (
    <div className="animate-pulse space-y-4">
      {[...Array(3)].map((_, i) => (
        <div key={i} className="bg-white rounded-xl border border-gray-100 p-5 space-y-3">
          <div className="flex justify-between items-center">
            <div className="flex gap-2">
              <div className="h-5 bg-gray-200 rounded w-24" />
              <div className="h-5 bg-indigo-100 rounded-full w-28" />
            </div>
          </div>
          {[...Array(i + 4)].map((_, j) => (
            <div key={j} className="flex justify-between py-2.5 border-t border-gray-100 gap-4">
              <div className="space-y-1 flex-1">
                <div className="h-3 bg-gray-200 rounded w-48" />
                <div className="h-3 bg-gray-100 rounded w-28" />
              </div>
              <div className="h-5 bg-gray-100 rounded-full w-14" />
            </div>
          ))}
        </div>
      ))}
    </div>
  );
}

// Returns the count of parlays matching a given size (undefined = all)
function countForSize(parlays: Parlay[], size: number | undefined): number {
  if (size === undefined) return parlays.length;
  return parlays.filter((p) => p.size === size).length;
}

export default function Parlays() {
  const [allParlays, setAllParlays] = useState<Parlay[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sizeFilter, setSizeFilter] = useState<number | undefined>();

  useEffect(() => {
    getParlays()
      .then(setAllParlays)
      .catch(() => setError("Failed to load parlays"))
      .finally(() => setLoading(false));
  }, []);

  const parlays = useMemo(
    () => (sizeFilter ? allParlays.filter((p) => p.size === sizeFilter) : allParlays),
    [allParlays, sizeFilter]
  );

  return (
    <div className="space-y-6">
      {/* Page header + filter row */}
      <div className="flex flex-col sm:flex-row sm:items-center gap-4 justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Top Parlays</h1>
          <p className="text-gray-500 text-sm mt-1">Ranked by combined confidence</p>
        </div>

        {/* Size filter — shown even while loading so layout is stable */}
        <div className="flex items-center gap-1.5 flex-wrap">
          <span className="text-xs text-gray-400 mr-1 font-medium">Legs:</span>
          {([undefined, 4, 5, 6, 7] as const).map((s) => {
            const count = loading ? null : countForSize(allParlays, s);
            const active = sizeFilter === s;
            const isEmpty = !loading && count === 0;
            return (
              <button
                key={s ?? "all"}
                onClick={() => setSizeFilter(s)}
                disabled={isEmpty}
                className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors flex items-center gap-1.5 ${
                  active
                    ? "bg-indigo-600 text-white shadow-sm"
                    : isEmpty
                    ? "bg-gray-50 text-gray-300 cursor-not-allowed"
                    : "bg-gray-100 text-gray-600 hover:bg-gray-200"
                }`}
              >
                {s !== undefined ? `${s}-leg` : "All"}
                {count !== null && count > 0 && (
                  <span
                    className={`text-xs rounded-full px-1.5 py-px font-semibold ${
                      active ? "bg-indigo-500 text-white" : "bg-gray-200 text-gray-500"
                    }`}
                  >
                    {count}
                  </span>
                )}
              </button>
            );
          })}
        </div>
      </div>

      {loading && <ParlaySkeleton />}

      {error && (
        <div className="flex items-start gap-3 bg-red-50 border border-red-200 text-red-700 rounded-xl p-4">
          <svg className="w-5 h-5 mt-0.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3m0 3h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" />
          </svg>
          <div>
            <div className="font-semibold text-sm">Unable to load parlays</div>
            <div className="text-xs mt-0.5 text-red-500">Make sure the backend is running on port 8000</div>
          </div>
        </div>
      )}

      {/* Empty states */}
      {!loading && !error && allParlays.length === 0 && (
        <div className="text-center py-20 px-6">
          <div className="text-4xl mb-3">⏳</div>
          <div className="text-gray-700 font-semibold">Parlays are warming up</div>
          <div className="text-gray-400 text-sm mt-1 max-w-xs mx-auto">
            Predictions are still loading. Check back in a moment — this takes about 60 seconds on a cold start.
          </div>
        </div>
      )}

      {!loading && !error && allParlays.length > 0 && parlays.length === 0 && (
        <div className="text-center py-16 text-gray-400">
          <div className="text-2xl mb-2">🔍</div>
          <div className="font-medium text-gray-500">No parlays match this filter</div>
          <button
            onClick={() => setSizeFilter(undefined)}
            className="mt-3 text-sm text-indigo-600 hover:underline"
          >
            Clear filter
          </button>
        </div>
      )}

      {/* Parlay cards */}
      <div className="space-y-4">
        {parlays.map((parlay, idx) => {
          const hasOdds = parlay.combined_odds > 0;
          return (
            <div
              key={idx}
              className="bg-white rounded-xl border border-gray-100 shadow-sm overflow-hidden"
            >
              {/* Card header */}
              <div className="px-5 pt-4 pb-3 flex items-center justify-between gap-3">
                <div className="flex items-center gap-2.5 flex-wrap">
                  <span className="text-sm font-bold text-gray-900">
                    {parlay.size}-Leg Parlay
                  </span>
                  {/* Confidence pill — the headline number */}
                  <span className="text-sm font-semibold text-indigo-700 bg-indigo-50 border border-indigo-100 px-2.5 py-0.5 rounded-full tabular-nums">
                    {(parlay.combined_prob * 100).toFixed(1)}% confidence
                  </span>
                </div>
                {hasOdds && (
                  <div className="text-right shrink-0">
                    <div className="text-xs text-gray-400">Combined odds</div>
                    <div className="text-sm font-bold text-gray-800 tabular-nums">
                      {parlay.combined_odds.toFixed(2)}x
                    </div>
                  </div>
                )}
              </div>

              {/* Leg list */}
              <div className="divide-y divide-gray-50 border-t border-gray-100">
                {parlay.legs.map((leg, li) => {
                  const legHasOdds = leg.decimal_odds > 0;
                  const { market, outcome } = parseLegLabels(leg);
                  const kickoffTime = new Date(leg.kickoff).toLocaleTimeString(undefined, {
                    hour: "2-digit",
                    minute: "2-digit",
                  });
                  return (
                    <div
                      key={li}
                      className="px-5 py-3 flex items-center justify-between gap-4"
                    >
                      {/* Left: match + pick */}
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="font-semibold text-gray-900 text-sm">
                            {outcome}
                          </span>
                          <span className="text-xs text-gray-400 bg-gray-100 px-1.5 py-0.5 rounded font-medium">
                            {market}
                          </span>
                        </div>
                        <div className="text-xs text-gray-400 mt-0.5 truncate">
                          {leg.home_team} vs {leg.away_team}
                          <span className="mx-1">·</span>
                          {kickoffTime}
                        </div>
                      </div>

                      {/* Right: confidence + optional odds */}
                      <div className="flex items-center gap-2 shrink-0">
                        <ProbBadge prob={leg.model_prob} />
                        {legHasOdds && (
                          <span className="text-xs text-gray-400 tabular-nums hidden sm:inline">
                            {leg.decimal_odds.toFixed(2)}x
                          </span>
                        )}
                        {legHasOdds && leg.edge > 0 && (
                          <span className="text-xs font-semibold text-emerald-700 hidden sm:inline">
                            +{(leg.edge * 100).toFixed(1)}%
                          </span>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Footer: EV only when odds are available */}
              {hasOdds && (
                <div className="px-5 py-2.5 border-t border-gray-100 bg-gray-50 flex justify-end text-xs text-gray-500">
                  Expected value:{" "}
                  <span
                    className={`ml-1 font-semibold ${
                      parlay.expected_value >= 0 ? "text-emerald-700" : "text-red-500"
                    }`}
                  >
                    {parlay.expected_value >= 0 ? "+" : ""}
                    {(parlay.expected_value * 100).toFixed(1)}%
                  </span>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
