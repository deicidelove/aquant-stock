import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";

const mutate = vi.fn();
vi.mock("../hooks/queries", () => ({
  useHoldings: () => ({ isSuccess: true, data: { rows: [{ code: "600000", name: "浦发", shares: 1000, avg_cost: 11, last_price: 13.95, market_value: 13950, unrealized: 2950, unrealized_pct: 26.8, alerts: [] }] } }),
  useTrades: () => ({ isSuccess: true, data: { rows: [] } }),
  usePnl: () => ({ isSuccess: true, data: { realized: 0, unrealized: 2950, total: 2950 } }),
  useAddTrade: () => ({ mutate }),
  useDeleteTrade: () => ({ mutate }),
}));
import AssistHoldings from "./AssistHoldings";

describe("AssistHoldings", () => {
  it("renders holdings, pnl and trade form", () => {
    render(<MemoryRouter><AssistHoldings /></MemoryRouter>);
    expect(screen.getByText("我的持仓")).toBeInTheDocument();
    expect(screen.getByText("盈亏汇总")).toBeInTheDocument();
    expect(screen.getByText("录入交易")).toBeInTheDocument();
    expect(screen.getByText("浦发")).toBeInTheDocument();
  });
});
