import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";

vi.mock("../hooks/queries", () => ({
  useLhbToday: () => ({
    isSuccess: true, isLoading: false,
    data: {
      date: "2026-07-03",
      rows: [
        { code: "002056", name: "横店东磁", pct_chg: 10.0, lhb_net_buy: 5.5e8, lhb_amount: 2e9, reason: "涨幅偏离", tags: ["机构", "北向", "佛山无影脚"] },
      ],
    },
  }),
  useLhbStock: () => ({
    isSuccess: true, isLoading: false,
    data: { code: "002056", name: "横店东磁", date: "2026-07-03", reason: "涨幅偏离",
      buy: [{ rank: 1, seat: "机构专用", buy: 3e7, sell: 0, net: 3e7, seat_type: "inst", hotmoney_name: null }],
      sell: [] },
  }),
}));
import Lhb from "./Lhb";

describe("Lhb page", () => {
  it("renders today rows with tags + date", () => {
    render(<MemoryRouter><Lhb /></MemoryRouter>);
    expect(screen.getByText("横店东磁")).toBeInTheDocument();
    expect(screen.getByText("2026-07-03")).toBeInTheDocument();
    expect(screen.getByText("佛山无影脚")).toBeInTheDocument();
    expect(screen.getByText("5.50亿")).toBeInTheDocument();
  });

  it("expands seat drawer on row click", () => {
    render(<MemoryRouter><Lhb /></MemoryRouter>);
    fireEvent.click(screen.getByText("横店东磁").closest("tr")!);
    expect(screen.getByText("买入前五")).toBeInTheDocument();
  });
});
