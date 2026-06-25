import { useQuery } from "@tanstack/react-query";
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
