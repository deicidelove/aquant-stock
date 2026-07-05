import { describe, it, expect, vi } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import React from "react";

vi.mock("../api/client", () => ({
  getRegime: vi.fn(async () => ({ state: "均衡", score: 3 })),
  getIndexSeries: vi.fn(async () => ({ code: "sh000300", points: [{ date: "d", close: 3900, ma20: 3890, ma60: 3850 }] })),
}));
import { useRegime, useIndexSeries } from "./queries";

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>;
}

describe("kandapan hooks", () => {
  it("useRegime returns state", async () => {
    const { result } = renderHook(() => useRegime(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data!.state).toBe("均衡");
  });
  it("useIndexSeries returns points", async () => {
    const { result } = renderHook(() => useIndexSeries(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data!.points[0].close).toBe(3900);
  });
});
