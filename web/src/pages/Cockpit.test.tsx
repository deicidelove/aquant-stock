import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
vi.mock("../charts/EChart", () => ({ default: () => <div data-testid="echart" /> }));
vi.mock("../hooks/queries", () => ({
  useRegime: () => ({ isSuccess: true, data: { state: "防守", score: 1, suggested_position: "1~3成", note: "宽度走弱" } }),
  useIndexSeries: () => ({ isSuccess: true, data: { code: "sh000300", points: [{ date: "d", close: 3900, ma20: 3890, ma60: 3850 }] } }),
  useAmountTrend: () => ({ isSuccess: true, data: { series: [{ date: "d", amount: 9000 }] } }),
  useSentiment: () => ({ isSuccess: true, data: { up: 1715, down: 1618, limit_up: 40, limit_down: 5, amount: 9e11, score: 37, label: "偏冷" } }),
  useMarketFund: () => ({ isSuccess: true, data: { today: -434, series: [{ date: "d", net: -434 }] } }),
  useSectorFund: () => ({ isSuccess: true, data: { as_of: "d", rows: [{ sector: "医药", pct_chg: 2, main_net: 5e8, main_net_pct: 1, leader: "恒瑞" }] } }),
  useAbnormal: () => ({ isSuccess: true, data: { scope: "stock", rows: [] } }),
}));
import Cockpit from "./Cockpit";

describe("Cockpit 看大盘", () => {
  it("renders verdict + index trend + amount + sentiment", () => {
    render(<MemoryRouter><Cockpit /></MemoryRouter>);
    expect(screen.getByText("今日研判")).toBeInTheDocument();
    expect(screen.getByText("防守")).toBeInTheDocument();
    expect(screen.getByText(/沪深300 走势/)).toBeInTheDocument();
    expect(screen.getByText("两市量能")).toBeInTheDocument();
    expect(screen.getByText("市场情绪")).toBeInTheDocument();
  });
});
