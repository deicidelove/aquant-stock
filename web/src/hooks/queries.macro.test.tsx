import { describe, it, expect, vi } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import React from "react";

vi.mock("../api/client", () => ({
  getSentimentMacro: vi.fn(async () => ({ up: 1, down: 2, limit_up: 0, limit_down: 0, amount: 0, score: 42, label: "中性" })),
  getSectorFund: vi.fn(async () => ({ as_of: "2026-06-23", rows: [{ sector: "医药", pct_chg: 2, main_net: 5e8, main_net_pct: 1, leader: "恒瑞" }] })),
}));
import { useSentiment, useSectorFund } from "./queries";

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>;
}

describe("macro hooks", () => {
  it("useSentiment returns data", async () => {
    const { result } = renderHook(() => useSentiment(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data!.label).toBe("中性");
  });
  it("useSectorFund returns rows", async () => {
    const { result } = renderHook(() => useSectorFund(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data!.rows[0].sector).toBe("医药");
  });
});
