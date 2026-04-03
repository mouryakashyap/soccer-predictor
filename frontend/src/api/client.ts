import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000",
});

export interface Fixture {
  fixture_id: string;
  home_team: string;
  away_team: string;
  kickoff: string;
  league: string;
  competition_code: string;
  season: number;
  home_team_id?: number;
  away_team_id?: number;
  odds?: {
    h2h: { home: number; draw: number; away: number };
    totals: { over: number; under: number };
    btts: { yes: number; no: number };
  };
}

export interface ValueBet {
  fixture_id: string;
  market: string;
  outcome: string;
  model_prob: number;
  implied_prob: number;
  edge: number;
  decimal_odds: number;
  is_value: boolean;
}

export interface PredictionResult {
  fixture: Fixture;
  predictions: {
    h2h: { home_win: number; draw: number; away_win: number };
    totals: { over_2_5: number; under_2_5: number };
    btts: { yes: number; no: number };
  };
  value_bets: ValueBet[];
}

export interface ParlayLeg {
  fixture_id: string;
  market: string;
  outcome: string;
  model_prob: number;
  decimal_odds: number;
  edge: number;
  home_team: string;
  away_team: string;
  league: string;
  kickoff: string;
}

export interface Parlay {
  size: number;
  legs: ParlayLeg[];
  combined_prob: number;
  combined_odds: number;
  expected_value: number;
}

export const getFixtures = () => api.get<Fixture[]>("/fixtures").then((r) => r.data);
export const getPredictions = () => api.get<PredictionResult[]>("/predictions").then((r) => r.data);
export const getParlays = (size?: number, minEv?: number) => {
  const params: Record<string, unknown> = {};
  if (size) params.size = size;
  if (minEv !== undefined) params.min_ev = minEv;
  return api.get<Parlay[]>("/parlays", { params }).then((r) => r.data);
};
