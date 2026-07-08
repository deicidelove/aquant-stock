import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import ScorecardSummary from "./ScorecardSummary";

const data = {
  sample: { picks: 780, snapshots: 26, start: "2025-06-03", end: "2026-06-10", live: 30, replay: 750 },
  horizons: [
    { h: 5, settled: 750, pending: 0, mean_excess: -0.0009, win_rate: 0.4133, mean_ret: 0.0016 },
    { h: 60, settled: 570, pending: 180, mean_excess: 0.0292, win_rate: 0.4474, mean_ret: 0.082 },
  ],
  rank_ic: [{ h: 5, n: 26, mean_ic: 0.0074, ir: 0.032 }],
  delisted: 1,
};

describe("ScorecardSummary", () => {
  it("renders sample + horizon rows + rank-ic + delisted", () => {
    render(<ScorecardSummary data={data} />);
    expect(screen.getByText(/样本 780 条/)).toBeInTheDocument();
    expect(screen.getByText("+2.92%")).toBeInTheDocument();  // T+60 超额
    expect(screen.getByText("44.74%")).toBeInTheDocument();  // 胜率
    expect(screen.getByText(/含 1 条停牌\/退市/)).toBeInTheDocument();
  });

  it("empty hint when no picks", () => {
    render(<ScorecardSummary data={{ ...data, sample: { ...data.sample, picks: 0 }, horizons: [] }} />);
    expect(screen.getByText(/暂无推荐台账/)).toBeInTheDocument();
  });
});
