import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import * as api from "../api/client";
import { refetchIntervalMs } from "../lib/tradingHours";

const live = () => refetchIntervalMs(new Date());

export const useOverview = () =>
  useQuery({ queryKey: ["overview"], queryFn: api.getOverview, refetchInterval: live });

export const useSectors = () =>
  useQuery({ queryKey: ["sectors"], queryFn: api.getSectors, refetchInterval: live });

export const useTopScores = (top = 20) =>
  useQuery({ queryKey: ["top-scores", top], queryFn: () => api.getTopScores(top), refetchInterval: live });

export const usePicks = (top = 3) =>
  useQuery({ queryKey: ["picks", top], queryFn: () => api.getPicks(top), refetchInterval: live });

export const useKline = (code: string, n = 250) =>
  useQuery({ queryKey: ["kline", code, n], queryFn: () => api.getKline(code, n), enabled: !!code });

export const useReport = (code: string) =>
  useQuery({ queryKey: ["report", code], queryFn: () => api.getReport(code), enabled: !!code });

export const useHoldings = () =>
  useQuery({ queryKey: ["holdings"], queryFn: api.getHoldings, refetchInterval: live });

export const useTrades = () =>
  useQuery({ queryKey: ["trades"], queryFn: api.getTrades });

export const usePnl = () =>
  useQuery({ queryKey: ["pnl"], queryFn: api.getPnl, refetchInterval: live });

export const useBriefing = (top = 12) =>
  useQuery({ queryKey: ["briefing", top], queryFn: () => api.getBriefing(top) });

export const useScorecard = () =>
  useQuery({ queryKey: ["scorecard"], queryFn: api.getScorecard });

function useInvalidateHoldings() {
  const qc = useQueryClient();
  return () => {
    qc.invalidateQueries({ queryKey: ["holdings"] });
    qc.invalidateQueries({ queryKey: ["trades"] });
    qc.invalidateQueries({ queryKey: ["pnl"] });
  };
}

export const useAddTrade = () => {
  const invalidate = useInvalidateHoldings();
  return useMutation({ mutationFn: api.addTrade, onSuccess: invalidate });
};

export const useDeleteTrade = () => {
  const invalidate = useInvalidateHoldings();
  return useMutation({ mutationFn: api.deleteTrade, onSuccess: invalidate });
};

const jobPoll = (q: { state: { data?: { status?: string } } }) => {
  const s = q.state.data?.status;
  return s === "done" || s === "error" ? false : 1500;
};

export const useQuantWeights = () =>
  useQuery({ queryKey: ["quant-weights"], queryFn: api.getQuantWeights });

export const useSubmitBacktest = () =>
  useMutation({ mutationFn: api.submitBacktest });

export const useBacktestJob = (jobId: string | null) =>
  useQuery({
    queryKey: ["backtest-job", jobId],
    queryFn: () => api.getBacktestJob(jobId as string),
    enabled: !!jobId,
    refetchInterval: jobPoll as unknown as number | false,
  });

export const useSubmitFactorIc = () =>
  useMutation({ mutationFn: api.submitFactorIc });

export const useFactorIcJob = (jobId: string | null) =>
  useQuery({
    queryKey: ["factor-ic-job", jobId],
    queryFn: () => api.getFactorIcJob(jobId as string),
    enabled: !!jobId,
    refetchInterval: jobPoll as unknown as number | false,
  });

export const useIndices = () =>
  useQuery({ queryKey: ["m-indices"], queryFn: api.getIndices, refetchInterval: live });
export const useSentiment = () =>
  useQuery({ queryKey: ["m-sentiment"], queryFn: api.getSentimentMacro, refetchInterval: live });
export const useMarketFund = (days = 10) =>
  useQuery({ queryKey: ["m-marketfund", days], queryFn: () => api.getMarketFund(days), refetchInterval: live });
export const useSectorFund = () =>
  useQuery({ queryKey: ["m-sectorfund"], queryFn: api.getSectorFund, refetchInterval: live });
export const useAbnormal = (scope = "stock", n = 20, z = 2) =>
  useQuery({ queryKey: ["m-abnormal", scope, n, z], queryFn: () => api.getAbnormal(scope, n, z), refetchInterval: live });

export const useBoard = () =>
  useQuery({ queryKey: ["board"], queryFn: api.getBoard, refetchInterval: live });

export const useWatchlist = () =>
  useQuery({ queryKey: ["watchlist"], queryFn: api.getWatchlist });

function useInvalidateBoard() {
  const qc = useQueryClient();
  return () => {
    qc.invalidateQueries({ queryKey: ["board"] });
    qc.invalidateQueries({ queryKey: ["watchlist"] });
  };
}

export const useAddWatch = () => {
  const invalidate = useInvalidateBoard();
  return useMutation({ mutationFn: api.addWatch, onSuccess: invalidate });
};

export const useRemoveWatch = () => {
  const invalidate = useInvalidateBoard();
  return useMutation({ mutationFn: api.removeWatch, onSuccess: invalidate });
};

export const useRegime = () =>
  useQuery({ queryKey: ["regime"], queryFn: api.getRegime, refetchInterval: live });
export const useIndexSeries = (code = "sh000300", n = 120) =>
  useQuery({ queryKey: ["index-series", code, n], queryFn: () => api.getIndexSeries(code, n), refetchInterval: live });
export const useAmountTrend = (days = 20) =>
  useQuery({ queryKey: ["amount-trend", days], queryFn: () => api.getAmountTrend(days), refetchInterval: live });

export const useStockChart = (code: string, n = 250) =>
  useQuery({ queryKey: ["stock-chart", code, n], queryFn: () => api.getStockChart(code, n), enabled: !!code });

export const useLhbToday = (limit = 50) =>
  useQuery({ queryKey: ["lhb-today", limit], queryFn: () => api.getLhbToday(limit) });
export const useLhbStock = (code: string) =>
  useQuery({ queryKey: ["lhb-stock", code], queryFn: () => api.getLhbStock(code), enabled: !!code });

export const useNewsSentiment = (limit = 30) =>
  useQuery({ queryKey: ["news-sentiment", limit], queryFn: () => api.getNewsSentiment(limit), refetchInterval: live });

export const useLimitLadder = () =>
  useQuery({ queryKey: ["limit-ladder"], queryFn: api.getLimitLadder, refetchInterval: live });
export const useNorthFlow = () =>
  useQuery({ queryKey: ["north-flow"], queryFn: api.getNorthFlow, refetchInterval: live });

export const useAiReport = (code: string, polling = false) =>
  useQuery({
    queryKey: ["ai-report", code],
    queryFn: () => api.getAiReport(code),
    enabled: !!code,
    // 生成中(已触发但缓存还没落)时每 3 秒轮询，落库后停
    refetchInterval: (q) => (polling && !q.state.data?.report ? 3000 : false),
  });

export const useGenAiReport = (code: string) => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => api.genAiReport(code),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["ai-report", code] }),
  });
};
