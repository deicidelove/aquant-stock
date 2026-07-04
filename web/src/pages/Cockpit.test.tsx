import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
vi.mock("../charts/EChart", () => ({ default: () => <div data-testid="echart" /> }));
vi.mock("../hooks/queries", () => ({
  useIndices: () => ({ isSuccess: true, data: { rows: [{ code: "sh000300", close: 3900, ret_20d: 1 }] } }),
  useSentiment: () => ({ isSuccess: true, data: { up: 3000, down: 1000, limit_up: 40, limit_down: 5, amount: 9e11, score: 62, label: "偏热" } }),
  useMarketFund: () => ({ isSuccess: true, data: { today: 3.4, series: [{ date: "2026-06-23", net: 3.4 }] } }),
  useSectorFund: () => ({ isSuccess: true, data: { as_of: "2026-06-23", rows: [{ sector: "医药", pct_chg: 2, main_net: 5e8, main_net_pct: 1, leader: "恒瑞" }] } }),
  useAbnormal: () => ({ isSuccess: true, data: { scope: "stock", rows: [] } }),
}));
import Cockpit from "./Cockpit";

describe("Cockpit macro", () => {
  it("renders the five macro modules' titles", () => {
    render(<MemoryRouter><Cockpit /></MemoryRouter>);
    expect(screen.getByText("大盘指数")).toBeInTheDocument();
    expect(screen.getByText("市场情绪")).toBeInTheDocument();
    expect(screen.getByText("大盘资金")).toBeInTheDocument();
    expect(screen.getByText("板块资金")).toBeInTheDocument();
    expect(screen.getByText(/异常资金/)).toBeInTheDocument();
  });
});
