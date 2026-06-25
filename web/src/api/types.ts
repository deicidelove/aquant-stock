export interface Overview {
  breadth: Record<string, number>;
  regime: { state: string; score: number; suggested_position?: string; note?: string; [k: string]: unknown };
  index: { code: string; close: number; above_ma20?: boolean; above_ma60?: boolean; ret_20d?: number | null; ret_60d?: number | null };
}

export interface SectorRow { sector: string; pct_chg: number; mkt_cap?: number; [k: string]: unknown }
export interface Sectors { as_of: string | null; rows: SectorRow[]; rotation: Record<string, unknown> }

export interface ScoreRow { code: string; name: string; score: number }
export interface TopScores { as_of: string | null; rows: ScoreRow[] }

export interface PickRow { code: string; name: string; score: number; action?: string; close?: number; [k: string]: unknown }
export interface Picks { rows: PickRow[] }

export interface Bar { date: string; open: number; high: number; low: number; close: number; volume: number }
export interface Kline { code: string; bars: Bar[] }

export interface Decision {
  code: string; name: string; date: string; close: number;
  total_score: number; signal: string; one_liner: string; risk_level: string;
  risks: string[];
  battle_plan: { ideal_buy: number; secondary_buy: number; stop_loss: number; take_profit: number; position: string };
  checklist: string[];
  [k: string]: unknown;
}
export interface Report { code: string; decision: Decision }

export interface Holding {
  code: string; name: string; shares: number; avg_cost: number;
  last_price: number | null; market_value: number; unrealized: number;
  unrealized_pct: number; alerts: string[];
}
export interface HoldingsResp { rows: Holding[] }

export interface Trade { tid: number; date: string; code: string; side: string; shares: number; price: number; note: string }
export interface TradesResp { rows: Trade[] }

export interface Pnl { realized: number; unrealized: number; total: number }

export interface TradeInput { date: string; code: string; side: string; shares: number; price: number; note?: string }

export interface BriefingRow { code: string; name: string; [k: string]: unknown }
export interface BriefingResp { rows: BriefingRow[] }

export interface ScorecardResp { as_of: string | null; rows: Record<string, unknown>[] }
