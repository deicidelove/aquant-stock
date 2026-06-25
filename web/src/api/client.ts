import type { Overview, Sectors, TopScores, Picks, Kline, Report } from "./types";

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
