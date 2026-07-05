import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { vi } from "vitest";
vi.mock("../../charts/EChart", () => ({ default: () => <div data-testid="echart" /> }));
import IndicesPanel from "./IndicesPanel";
import SentimentPanel from "./SentimentPanel";
import MarketFundPanel from "./MarketFundPanel";
import SectorFundPanel from "./SectorFundPanel";
import AbnormalPanel from "./AbnormalPanel";

describe("macro panels", () => {
  it("IndicesPanel renders index close", () => {
    render(<IndicesPanel rows={[{ code: "sh000300", close: 3912.5, ret_20d: 2.1, ret_60d: 5 }]} />);
    expect(screen.getByText(/3912.5/)).toBeInTheDocument();
  });
  it("SentimentPanel renders label + score", () => {
    render(<SentimentPanel data={{ up: 3000, down: 1800, limit_up: 40, limit_down: 5, amount: 9e11, score: 62, label: "偏热" }} />);
    expect(screen.getByText("偏热")).toBeInTheDocument();
    expect(screen.getByText(/3000/)).toBeInTheDocument();
  });
  it("MarketFundPanel renders today + chart", () => {
    render(<MarketFundPanel data={{ today: 3.4, series: [{ date: "2026-06-23", net: 3.4 }] }} />);
    expect(screen.getByTestId("echart")).toBeInTheDocument();
  });
  it("SectorFundPanel renders chart + top sector", () => {
    render(<SectorFundPanel data={{ as_of: "2026-06-23", rows: [{ sector: "医药", pct_chg: 2, main_net: 5e8, main_net_pct: 1, leader: "恒瑞" }] }} />);
    expect(screen.getByText("医药")).toBeInTheDocument();
  });
  it("AbnormalPanel renders rows or empty", () => {
    render(<AbnormalPanel data={{ scope: "stock", rows: [{ key: "600000", latest: 5e8, mean: 1e7, std: 3e6, z: 12.3 }] }} />);
    expect(screen.getByText("600000")).toBeInTheDocument();
    render(<AbnormalPanel data={{ scope: "sector", rows: [] }} />);
    expect(screen.getByText(/暂无/)).toBeInTheDocument();
  });
});
