import type { PredictionResult } from "../api/client";
import { OUTCOME_LABEL, MARKET_LABEL } from "../lib/labels";
import ValueBadge from "./ValueBadge";

interface Props {
  result: PredictionResult;
}

// A probability bar row. The highest value in its group gets a stronger color.
function ProbRow({
  label,
  value,
  isTop,
}: {
  label: string;
  value: number;
  isTop: boolean;
}) {
  const pct = (value * 100).toFixed(1);
  return (
    <div className="mb-2">
      <div className="flex justify-between text-xs mb-0.5">
        <span
          className={isTop ? "text-gray-900 font-semibold" : "text-gray-500"}
        >
          {label}
        </span>
        <span
          className={
            isTop ? "font-bold text-indigo-700" : "font-medium text-gray-600"
          }
        >
          {pct}%
        </span>
      </div>
      <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full ${isTop ? "bg-indigo-500" : "bg-gray-300"}`}
          style={{ width: `${Math.min(value * 100, 100)}%` }}
        />
      </div>
    </div>
  );
}

function MarketPanel({
  title,
  entries,
}: {
  title: string;
  entries: [string, number][];
}) {
  // Find the key with the highest probability
  const maxVal = Math.max(...entries.map(([, v]) => v));

  return (
    <div className="bg-gray-50 rounded-lg p-3">
      <div className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-2.5">
        {title}
      </div>
      {entries.map(([k, v]) => (
        <ProbRow
          key={k}
          label={OUTCOME_LABEL[k] ?? k}
          value={v}
          isTop={v === maxVal}
        />
      ))}
    </div>
  );
}

export default function FixtureCard({ result }: Props) {
  const { fixture, predictions, value_bets } = result;

  // Show only HH:MM — the date heading in Dashboard already carries the date
  const kickoffTime = new Date(fixture.kickoff).toLocaleTimeString(undefined, {
    hour: "2-digit",
    minute: "2-digit",
  });

  const valueBets = value_bets.filter((b) => b.is_value);
  // Strongest edge bet for the accent strip, if any
  const topBet =
    valueBets.length > 0
      ? [...valueBets].sort((a, b) => b.edge - a.edge)[0]
      : null;

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
      {/* Top accent strip for value-bet fixtures */}
      {topBet && (
        <div className="h-1 bg-gradient-to-r from-indigo-500 to-emerald-400" />
      )}

      <div className="p-5 space-y-4">
        {/* Header */}
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            {/* Teams — the most critical piece of info */}
            <div className="text-base font-bold text-gray-900 leading-snug">
              {fixture.home_team}
              <span className="text-gray-400 font-normal mx-1.5">vs</span>
              {fixture.away_team}
            </div>
            <div className="text-xs text-gray-400 mt-0.5">{kickoffTime}</div>
          </div>
          {valueBets.length > 0 && (
            <div className="shrink-0 flex items-center gap-1.5 bg-emerald-50 border border-emerald-200 text-emerald-700 text-xs font-semibold px-2.5 py-1 rounded-full">
              <span className="inline-block w-1.5 h-1.5 rounded-full bg-emerald-500" />
              {valueBets.length} value bet{valueBets.length > 1 ? "s" : ""}
            </div>
          )}
        </div>

        {/* Probability grids */}
        <div className="grid grid-cols-3 gap-2.5">
          <MarketPanel
            title="1X2"
            entries={Object.entries(predictions.h2h) as [string, number][]}
          />
          <MarketPanel
            title="O/U 2.5"
            entries={Object.entries(predictions.totals) as [string, number][]}
          />
          <MarketPanel
            title="BTTS"
            entries={Object.entries(predictions.btts) as [string, number][]}
          />
        </div>

        {/* Value bets */}
        {valueBets.length > 0 && (
          <div className="border-t border-gray-100 pt-3 space-y-2">
            <div className="text-xs font-semibold text-gray-400 uppercase tracking-wide">
              Value Bets
            </div>
            {valueBets.map((b, i) => (
              <div
                key={i}
                className="flex items-center justify-between gap-3 text-sm bg-gray-50 rounded-lg px-3 py-2"
              >
                <div className="min-w-0">
                  {/* Pick is the primary label; market is secondary */}
                  <span className="font-semibold text-gray-900">
                    {OUTCOME_LABEL[b.outcome] ?? b.outcome}
                  </span>
                  <span className="text-gray-400 text-xs ml-1.5">
                    {MARKET_LABEL[b.market] ?? b.market}
                  </span>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  <span className="text-gray-500 text-xs tabular-nums">
                    {(b.model_prob * 100).toFixed(1)}% model
                    {b.decimal_odds > 0 && ` · ${b.decimal_odds}x`}
                  </span>
                  <ValueBadge edge={b.edge} />
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
