const BASE = process.env.AUREUM_API_URL ?? "http://localhost:8010";

export type MacroDay = {
  date: string;
  gold_usd: number;
  gold_return_1d: number | null;
  real_yield_10y: number | null;
  nominal_yield_10y: number | null;
  curve_10y_2y: number | null;
  usd_broad_index: number | null;
  vix: number | null;
};

export type IntradayBar = { minute: string; close: number; n_trades: number };

export type RiskDay = {
  event_date: string;
  n_events: number;
  avg_goldstein: number;
  avg_tone: number;
  conflict_article_share: number | null;
};

export type Positioning = {
  report_date: string;
  net_noncommercial: number;
  net_share_oi: number | null;
  positioning_zscore_3y: number | null;
};

export type EventOdds = {
  market_id: string;
  question: string;
  leading_outcome: string;
  leading_prob: number;
  volume_24h: number;
  end_date: string | null;
};

async function get<T>(path: string): Promise<T | null> {
  try {
    const res = await fetch(`${BASE}${path}`, { next: { revalidate: 60 } });
    if (!res.ok) return null;
    return (await res.json()) as T;
  } catch {
    return null; // API down → the section degrades visibly, the page never breaks
  }
}

export const fetchMacro = () => get<MacroDay[]>("/api/macro/daily?days=365");
export const fetchIntraday = () => get<IntradayBar[]>("/api/gold/intraday?hours=72");
export const fetchRisk = () => get<RiskDay[]>("/api/risk/daily?days=90");
export const fetchPositioning = () => get<Positioning[]>("/api/positioning?instrument=gold");
export const fetchOdds = () => get<EventOdds[]>("/api/odds?limit=12");
