import type { PredictionResult } from "../api/client";
import ValueBadge from "./ValueBadge";

interface Props {
  result: PredictionResult;
}

const OUTCOME_LABEL: Record<string, string> = {
  home_win: "Home Win",
  draw: "Draw",
  away_win: "Away Win",
  over_2_5: "Over 2.5",
  under_2_5: "Under 2.5",
  yes: "BTTS Yes",
  no: "BTTS No",
};

const MARKET_LABEL: Record<string, string> = {
  h2h: "1X2",
  totals: "O/U 2.5",
  btts: "BTTS",
};

export default function FixtureCard({ result }: Props) {
  const { fixture, predictions, value_bets } = result;
  const kickoff = new Date(fixture.kickoff).toLocaleString(undefined, {
    weekday: "short", month: "short", day: "numeric", hour: "2-digit", minute: "2-digit",
  });

  const valueBets = value_bets.filter((b) => b.is_value);

  return (
    <div className="bg-white rounded-xl shadow p-5 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="text-lg font-bold text-gray-900">
            {fixture.home_team} <span className="text-gray-400 font-normal">vs</span> {fixture.away_team}
          </div>
          <div className="text-xs text-gray-500 mt-0.5">{fixture.league} · {kickoff}</div>
        </div>
        {valueBets.length > 0 && (
          <span className="text-xs font-semibold px-2 py-1 rounded-full bg-indigo-100 text-indigo-700">
            {valueBets.length} value bet{valueBets.length > 1 ? "s" : ""}
          </span>
        )}
      </div>

      {/* Probabilities */}
      <div className="grid grid-cols-3 gap-3 text-sm">
        {/* 1X2 */}
        <div className="bg-gray-50 rounded-lg p-3">
          <div className="text-xs font-semibold text-gray-500 mb-2">1X2</div>
          {Object.entries(predictions.h2h).map(([k, v]) => (
            <div key={k} className="flex justify-between">
              <span className="text-gray-600">{OUTCOME_LABEL[k]}</span>
              <span className="font-medium">{(v * 100).toFixed(1)}%</span>
            </div>
          ))}
        </div>
        {/* O/U */}
        <div className="bg-gray-50 rounded-lg p-3">
          <div className="text-xs font-semibold text-gray-500 mb-2">O/U 2.5</div>
          {Object.entries(predictions.totals).map(([k, v]) => (
            <div key={k} className="flex justify-between">
              <span className="text-gray-600">{OUTCOME_LABEL[k]}</span>
              <span className="font-medium">{(v * 100).toFixed(1)}%</span>
            </div>
          ))}
        </div>
        {/* BTTS */}
        <div className="bg-gray-50 rounded-lg p-3">
          <div className="text-xs font-semibold text-gray-500 mb-2">BTTS</div>
          {Object.entries(predictions.btts).map(([k, v]) => (
            <div key={k} className="flex justify-between">
              <span className="text-gray-600">{OUTCOME_LABEL[k]}</span>
              <span className="font-medium">{(v * 100).toFixed(1)}%</span>
            </div>
          ))}
        </div>
      </div>

      {/* Value bets */}
      {valueBets.length > 0 && (
        <div className="border-t pt-3 space-y-1.5">
          <div className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Value Bets</div>
          {valueBets.map((b, i) => (
            <div key={i} className="flex items-center justify-between text-sm">
              <span className="text-gray-700">
                <span className="font-medium">{MARKET_LABEL[b.market]}</span>
                {" · "}
                {OUTCOME_LABEL[b.outcome]}
              </span>
              <div className="flex items-center gap-3">
                <span className="text-gray-500 text-xs">
                  {(b.model_prob * 100).toFixed(1)}% model · {b.decimal_odds}x odds
                </span>
                <ValueBadge edge={b.edge} />
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
