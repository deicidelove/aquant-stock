import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
vi.mock("../charts/EChart", () => ({ default: () => <div data-testid="echart" /> }));
vi.mock("../hooks/queries", () => ({
  useOverview: () => ({ isSuccess: true, isError: false, data: { breadth: { up: 3000, down: 1000, limit_up: 10, up_ratio: 60, above_ma20_pct: 55, above_ma60_pct: 48, total: 5000 }, regime: { state: "进攻", score: 4 }, index: { code: "sh000300", close: 3900 } } }),
  useSectors: () => ({ isSuccess: true, isError: false, data: { as_of: "2026-06-23", rows: [{ sector: "银行", pct_chg: 1.2, mkt_cap: 5e11 }], rotation: {} } }),
  usePicks: () => ({ isSuccess: true, isError: false, data: { rows: [{ code: "600000", name: "浦发", score: 1.2 }] } }),
  useTopScores: () => ({ isSuccess: true, isError: false, data: { as_of: "2026-06-23", rows: [{ code: "000001", name: "平安", score: 2.5 }] } }),
}));
import Cockpit from "./Cockpit";

describe("Cockpit", () => {
  it("renders all four panels' key content", () => {
    render(<MemoryRouter><Cockpit /></MemoryRouter>);
    expect(screen.getByText("进攻")).toBeInTheDocument();
    expect(screen.getByText("每日建仓名单")).toBeInTheDocument();
    expect(screen.getByText("综合分高分股")).toBeInTheDocument();
    expect(screen.getByText("板块概览")).toBeInTheDocument();
  });
});
