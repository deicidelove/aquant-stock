import type {
  Overview, Sectors, TopScores, Picks, Kline, Report,
  HoldingsResp, TradesResp, Pnl, TradeInput, BriefingResp, ScorecardResp,
} from "./types";

async function apiGet<T>(path: string): Promise<T> {
  const res = await fetch("/api" + path);
  if (!res.ok) throw new Error(`API ${path} failed: ${res.status}`);
  return (await res.json()) as T;
}

export const getOverview = () => apiGet<Overview>("/cockpit/overview");
export const getSectors = () => apiGet<Sectors>("/cockpit/sectors");
export const getTopScores = (top = 20) => apiGet<TopScores>(`/cockpit/top-scores?top=${top}`);
export const getPicks = (top = 3) => apiGet<Picks>(`/cockpit/picks?top=${top}`);
export const getKline = (code: string, n = 250) => apiGet<Kline>(`/stock/${code}/kline?n=${n}`);
export const getReport = (code: string) => apiGet<Report>(`/stock/${code}/report`);

async function apiSend<T>(path: string, method: "POST" | "DELETE", body?: unknown): Promise<T> {
  const res = await fetch("/api" + path, {
    method,
    headers: body !== undefined ? { "Content-Type": "application/json" } : undefined,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) throw new Error(`API ${path} failed: ${res.status}`);
  return (await res.json()) as T;
}

export const getHoldings = () => apiGet<HoldingsResp>("/holdings");
export const getTrades = () => apiGet<TradesResp>("/holdings/trades");
export const getPnl = () => apiGet<Pnl>("/holdings/pnl");
export const addTrade = (input: TradeInput) => apiSend<{ tid: number }>("/holdings/trade", "POST", input);
export const deleteTrade = (tid: number) => apiSend<{ deleted: number }>(`/holdings/trade/${tid}`, "DELETE");
export const getBriefing = (top = 12) => apiGet<BriefingResp>(`/assist/briefing?top=${top}`);
export const getScorecard = () => apiGet<ScorecardResp>("/assist/scorecard");
