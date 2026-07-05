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

export type QuantWeights = { ic: Record<string, number>; momentum: Record<string, number> };

export interface BacktestParams {
  capital: number; weights: string | Record<string, number>;
  top_n: number; rebalance_every: number; min_history: number;
  start?: string; end?: string;
}
export interface BacktestResult {
  nav: { date: string; equity: number; benchmark: number | null }[];
  metrics: Record<string, number>;
  top_n: number; rebalance_every: number;
}
export interface FactorIcRow { factor: string; ic_mean: number; ic_std: number; ir: number; ic_win: number; n: number }
export interface FactorIcResult { rows: FactorIcRow[]; fwd: number }

export interface QuantJob<T> { job_id: string; kind: string; status: string; result: T | null; error: string | null }

export interface IndexRow { code: string; close: number; above_ma20?: boolean; above_ma60?: boolean; ret_20d?: number | null; ret_60d?: number | null }
export interface IndicesResp { rows: IndexRow[] }
export interface Sentiment { up: number; down: number; limit_up: number; limit_down: number; amount: number; score: number; label: string }
export interface MarketFund { today: number; series: { date: string; net: number }[] }
export interface SectorFundRow { sector: string; pct_chg: number; main_net: number; main_net_pct: number; leader: string }
export interface SectorFund { as_of: string | null; rows: SectorFundRow[] }
export interface AbnormalRow { key: string; latest: number; mean: number; std: number; z: number }
export interface Abnormal { scope: string; rows: AbnormalRow[] }

export interface BoardCard {
  code: string; name: string; last_price: number | null; pct_chg: number | null;
  kline: { date: string; close: number }[];
  signal: string; one_liner: string;
  battle_plan: { ideal_buy?: number; secondary_buy?: number; stop_loss?: number; take_profit?: number; position?: string };
  risk_level: string; alerts: string[];
}
export interface BoardResp { rows: BoardCard[] }
export interface WatchlistResp { codes: string[] }

export interface Regime { state: string; score: number; suggested_position?: string; note?: string; breadth?: Record<string, number>; index?: Record<string, unknown> }
export interface IndexPoint { date: string; close: number; ma20: number | null; ma60: number | null }
export interface IndexSeries { code: string; points: IndexPoint[] }
export interface AmountTrend { series: { date: string; amount: number }[] }

export interface ChartBar { date: string; open: number; high: number; low: number; close: number; volume: number }
export interface StockChart { code: string; bars: ChartBar[]; ma: Record<string, (number | null)[]>; macd: Record<string, (number | null)[]> }
