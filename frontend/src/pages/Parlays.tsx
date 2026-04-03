import { useEffect, useState } from "react";
import { getParlays, type Parlay, type ParlayLeg } from "../api/client";

const OUTCOME_LABEL: Record<string, string> = {
  home_win: "Home Win", draw: "Draw", away_win: "Away Win",
  over_2_5: "Over 2.5", under_2_5: "Under 2.5",
  yes: "BTTS Yes", no: "BTTS No",
};

const MARKET_LABEL: Record<string, string> = {
  h2h: "1X2", totals: "O/U", btts: "BTTS",
};

function formatOutcome(leg: ParlayLeg): string {
  const market = MARKET_LABEL[leg.market] ?? leg.market;
  const outcome = OUTCOME_LABEL[leg.outcome] ?? leg.outcome;
  return `${market} — ${outcome}`;
}

function ProbBadge({ prob }: { prob: number }) {
  const pct = (prob * 100).toFixed(1);
  let cls = "bg-gray-100 text-gray-600";
  if (prob >= 0.7) cls = "bg-green-100 text-green-700";
  else if (prob >= 0.5) cls = "bg-yellow-100 text-yellow-700";
  return (
    <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${cls}`}>
      {pct}%
    </span>
  );
}

export default function Parlays() {
  const [parlays, setParlays] = useState<Parlay[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sizeFilter, setSizeFilter] = useState<number | undefined>();

  useEffect(() => {
    setLoading(true);
    getParlays(sizeFilter)
      .then(setParlays)
      .catch(() => setError("Failed to load parlays"))
      .finally(() => setLoading(false));
  }, [sizeFilter]);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Top Parlays</h1>
          <p className="text-gray-500 text-sm mt-1">Ranked by confidence</p>
        </div>
        <div className="flex gap-2">
          {([undefined, 4, 5, 6, 7] as const).map((s) => (
            <button
              key={s ?? "all"}
              onClick={() => setSizeFilter(s)}
              className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                sizeFilter === s
                  ? "bg-indigo-600 text-white"
                  : "bg-gray-100 text-gray-600 hover:bg-gray-200"
              }`}
            >
              {s !== undefined ? `${s}-leg` : "All"}
            </button>
          ))}
        </div>
      </div>

      {loading && <div className="text-center py-16 text-gray-400">Loading parlays...</div>}
      {error && <div className="bg-red-50 text-red-700 rounded-lg p-4">{error}</div>}
      {!loading && !error && parlays.length === 0 && (
        <div className="text-center py-16 text-gray-400">No parlays found</div>
      )}

      <div className="space-y-4">
        {parlays.map((parlay, idx) => {
          const hasOdds = parlay.combined_odds > 0;
          return (
            <div key={idx} className="bg-white rounded-xl shadow p-5 space-y-3">
              {/* Parlay header */}
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <span className="text-sm font-bold text-gray-900">
                    {parlay.size}-Leg Parlay
                  </span>
                  <span className="text-sm font-semibold text-indigo-700 bg-indigo-50 px-2.5 py-0.5 rounded-full">
                    {(parlay.combined_prob * 100).toFixed(1)}% confidence
                  </span>
                </div>
                {hasOdds && (
                  <div className="text-right">
                    <div className="text-xs text-gray-500">Combined odds</div>
                    <div className="text-sm font-bold text-gray-800">
                      {parlay.combined_odds.toFixed(2)}x
                    </div>
                  </div>
                )}
              </div>

              {/* Legs */}
              <div className="divide-y divide-gray-100">
                {parlay.legs.map((leg, li) => {
                  const legHasOdds = leg.decimal_odds > 0;
                  return (
                    <div key={li} className="py-2.5 flex items-start justify-between gap-4 text-sm">
                      <div className="min-w-0">
                        <div className="font-medium text-gray-900 truncate">
                          {leg.home_team} vs {leg.away_team}
                        </div>
                        <div className="text-gray-400 text-xs mt-0.5">{leg.league}</div>
                      </div>
                      <div className="flex items-center gap-3 shrink-0">
                        <span className="text-gray-600 text-xs">{formatOutcome(leg)}</span>
                        <ProbBadge prob={leg.model_prob} />
                        {legHasOdds && (
                          <>
                            <span className="text-gray-500 text-xs">{leg.decimal_odds.toFixed(2)}x</span>
                            <span className="text-xs font-medium text-green-700">
                              +{(leg.edge * 100).toFixed(1)}% edge
                            </span>
                          </>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Footer: EV only when odds are available */}
              {hasOdds && (
                <div className="pt-1 border-t border-gray-100 text-right text-xs text-gray-500">
                  Expected value:{" "}
                  <span className={parlay.expected_value >= 0 ? "text-green-700 font-semibold" : "text-red-500 font-semibold"}>
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
